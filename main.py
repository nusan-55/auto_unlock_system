#-*-coding : UTF-8 -*-
# 2022/09/04 hc595_shift関数を追加
# clearDisplayを編集
import RPi.GPIO as GPIO
import time
import sys
import math


#GPIO 02 03 04 17 27 22 09 11 05 06  13    19    20
#pin  03 05 07 11 13 15 21 23 29 31  33    35    38
#sw   00 01 02 03 04 05 06 07 08 09 toggle enter unlock

#スイッチのピン番号
sw_pins = [ 3, 5, 7, 11, 13, 15, 21, 23, 29, 31, 33, 35, 38 ]
#ブザーのピン
buzzer_pin = 37
#サーボのピン
servo_pin = 18
#解錠のピン
unlock_pin = 38
#LED赤のピン
LED_red_pin = 22
#LED緑のピン
LED_green_pin = 24

#7セグLEDの桁
seg_place_pins = [ 8, 12, 16, 19 ]
#16進数の0～9のセグメントコード配列（アノードコモン）
number = ( 0xc0, 0xf9, 0xa4, 0xb0, 0x99, 0x92, 0x82, 0xf8, 0x80, 0x90 )
#解錠の際のHexコード
OPEN = [ 0xc0, 0x8c, 0x86, 0xc8 ]
#入力を間違った際のHexコード
Error = [ 0x86, 0xaf, 0xaf ]
SDI = 36
SRCLK = 26
RCLK = 32

#使用する各社サーボの駆動パルス
T = 14 # パルス周期[mSec]
f = round( 1/T * 1000, 1 ) # 周波数
neutral = 1520 / 1000 # ニュートラル1500 [ μSec → mSec ]
variable = 500 / 1000 # 可変範囲±600 [ μSec → mSec ]

#入力した数字を隠蔽するかどうか
hiding = True

def setup():
        GPIO.setmode( GPIO.BOARD )
        #スイッチにプルアップ抵抗を設定
        for num in sw_pins:
                GPIO.setup( num, GPIO.IN, pull_up_down = GPIO.PUD_UP )
        #セレクトピンのGPIOを出力に設定する。
        for num in seg_place_pins:
                GPIO.setup( num, GPIO.OUT )
        #シフトレジストのGPIOをセットアップ
        GPIO.setup( SDI, GPIO.OUT )
        GPIO.setup( RCLK, GPIO.OUT )
        GPIO.setup( SRCLK, GPIO.OUT )
        #ブザーのGPIOをセットアップ
        GPIO.setup( buzzer_pin, GPIO.OUT, initial=GPIO.LOW )

        #サーボのGPIOをセットアップ
        GPIO.setup( servo_pin, GPIO.OUT )

        #解錠ボタンのGPIOをセットアップ
        GPIO.setup( unlock_pin, GPIO.IN, pull_up_down = GPIO.PUD_UP )

        #LED赤のGPIOをセットアップ
        GPIO.setup( LED_red_pin, GPIO.OUT )

        #LED緑のGPIOをセットアップ
        GPIO.setup( LED_green_pin, GPIO.OUT, initial=GPIO.HIGH )

def clearDisplay():
        for i in range( 8 ):
                GPIO.output( SDI, 1 )
                GPIO.output( SRCLK, GPIO.HIGH )
                GPIO.output( SRCLK, GPIO.LOW )
        GPIO.output( RCLK, GPIO.HIGH )
        GPIO.output( RCLK, GPIO.LOW )

def pickDigit( digit ):
        for num in seg_place_pins:
                GPIO.output( num, GPIO.LOW )
        GPIO.output( seg_place_pins[digit], GPIO.HIGH )

def servo_degree( degree ):
        servo = GPIO.PWM( servo_pin, f )
        servo.start( 0.0 )
        duty = (( neutral + ( degree * variable / 90 )) / T ) * 100
        servo.ChangeDutyCycle( duty )
        time.sleep( 0.5 )
        servo.stop()

def hc595_shift(data):
        for i in range(8):
                GPIO.output( SDI, 0x80 & ( data << i ))
                GPIO.output( SRCLK, GPIO.HIGH )
                GPIO.output( SRCLK, GPIO.LOW )
        GPIO.output( RCLK, GPIO.HIGH )
        GPIO.output( RCLK, GPIO.LOW )

# 押されたスイッチを一つだけ取得する
def stand_by_number( in_num ):

        print( "ボタン待機中..." )
        i = 0
        while True:
                # SWが押されていた場合表示
                if len( in_num ) != 0:

                        clearDisplay()
                        pickDigit( i )
                        if hiding:
                                hc595_shift( 0xbf )
                        else:
                                hc595_shift( number[in_num[ i ]] )
                        time.sleep( 0.005 )
                for num in range( len( sw_pins )):
                        # スイッチピンが押されたことを検知
                        if GPIO.input( sw_pins[num] ) == False:
                                clearDisplay()
                                time.sleep( 0.2 )
                                print( "pushed GPIO pin number : " + str(sw_pins[num]) )
                                buzzer( onkai( 51 ), 0.2 )
                                #ボタンの番号を返す
                                return num
                if i > 2 or i > len( in_num ) - 2 :
                        i = 0
                else:
                        i = i + 1
def buzzer( freq, rhythm ):
        p = GPIO.PWM( buzzer_pin, 1 )
        p.start( 50 )
        p.ChangeFrequency( freq )
        time.sleep( rhythm )
        p.stop()


def onkai( n ):
        return 27.500*math.pow(math.pow(2,1/12),n)
def usage():
        print( "Usage : python main.py {pin1} {pin2} {pin3} {pin4}" )

def main():
        global hiding
        setup()
        clearDisplay()
        input_number = []
        if len( sys.argv ) < 2 :
                usage()
        #パスワードはコマンドライン引数で設定する（４桁）
        password = [ int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]) ]
        servo_degree( 0 )
        while True:
                try:
                        sw_number = stand_by_number( input_number )
                        # sw_number = 0,   1,   2,   3,   4,   5,   6,   7,   8,   9,   10,     11,   12
                        # sw_name   = SW0, SW1, SW2, SW3, SW4, SW5, SW6, SW7, SW8, SW9, toggle, enter unlock
                        if sw_number == 11:
                                if input_number == password:
                                        print( "入力した番号" + str(input_number) )
                                        print( "暗証番号" + str(password) )
                                        print( "解錠します" )
                                        servo_degree( 180 )
                                        for s in range(0, 50):
                                                for t in range(0, 4):
                                                        clearDisplay()
                                                        pickDigit( t )
                                                        hc595_shift( OPEN[t] )
                                                        time.sleep( 0.005 )
                                        clearDisplay()
                                        what_if()
                                        servo_degree( 0 )
                                        input_number = []
                                else:
                                        GPIO.output( LED_red_pin, GPIO.HIGH )
                                        GPIO.output( LED_green_pin, GPIO.LOW )

                                        for s in range(0, 100):
                                                for t in range(0, 3):
                                                        clearDisplay()
                                                        pickDigit( t )
                                                        hc595_shift( Error[t] )
                                                        time.sleep( 0.005 )
                                        GPIO.output( LED_red_pin, GPIO.LOW )
                                        GPIO.output( LED_green_pin, GPIO.HIGH )

                                        clearDisplay()
                                        print("暗証番号が違います")
                                        print("入力した番号" + str( input_number ))
                                        buzzer( onkai( 39 ), 0.5 )
                                        time.sleep( 0.2 )
                                        buzzer( onkai( 39 ), 0.5 )
                                        print("暗証番号" + str( password ) )
                                        input_number = []
                        elif sw_number == 12:
                                servo_degree( 180 )
                                what_if()
                                servo_degree( 0 )
                        elif sw_number == 10:
                                hiding = not hiding
                                print("7セグメントの番号を表示します")
                                print(input_number)
                        else:
                                print( "スイッチ番号:" + str(sw_number) )
                                input_number.append( sw_number )


                except KeyboardInterrupt:
                        print("テストを終了します")
                        GPIO.cleanup()
                        sys.exit()
#what ifメロディ
def what_if():
        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 24 ), 0.5 )#ra
        buzzer( onkai( 31 ), 0.5 )#mi
        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 29 ), 0.5 )#re
        buzzer( onkai( 20 ), 0.5 )#fa

        buzzer( onkai( 29 ), 0.3 )#re
        buzzer( onkai( 31 ), 0.3 )#mi
        buzzer( onkai( 32 ), 0.3 )#fa

        buzzer( onkai( 32 ), 0.5 )#fa
        buzzer( onkai( 26 ), 0.5 )#si
        buzzer( onkai( 34 ), 0.5 )#so
        buzzer( onkai( 22 ), 0.5 )#so
        buzzer( onkai( 31 ), 0.9 )#mi
        buzzer( onkai( 38 ), 0.9 )#si

        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 24 ), 0.5 )#ra
        buzzer( onkai( 31 ), 0.5 )#mi
        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 29 ), 0.5 )#re
        buzzer( onkai( 20 ), 0.5 )#fa

        buzzer( onkai( 29 ), 0.3 )#re
        buzzer( onkai( 31 ), 0.3 )#mi
        buzzer( onkai( 32 ), 0.3 )#fa

        buzzer( onkai( 34 ), 0.9 )#so
        buzzer( onkai( 32 ), 0.9 )#fa
        buzzer( onkai( 31 ), 0.9 )#mi
        buzzer( onkai( 38 ), 0.9 )#si

        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 24 ), 0.5 )#ra
        buzzer( onkai( 31 ), 0.5 )#mi
        buzzer( onkai( 36 ), 0.5 )#ra
        buzzer( onkai( 29 ), 0.5 )#re
        buzzer( onkai( 20 ), 0.5 )#fa

        buzzer( onkai( 29 ), 0.3 )#re
        buzzer( onkai( 31 ), 0.3 )#mi
        buzzer( onkai( 32 ), 0.3 )#fa

        buzzer( onkai( 32 ), 0.9 )#fa
        buzzer( onkai( 34 ), 0.9 )#so
        buzzer( onkai( 31 ), 1.1 )#mi
        time.sleep( 0.1 )
        buzzer( onkai( 29 ), 0.9 )#re
        buzzer( onkai( 29 ), 1.5 )#re

if __name__=="__main__":
        print("プログラムスタート")
        main()
        
