# ******************************************************************************************
# FileName     : Kit_SmartFactory2_IoT_test.py
# Description  :
# Author       : 박은정
# Created Date : 2024.09.11 : PEJ
# Reference    : AWS
# ******************************************************************************************
board_firmware_version = 'smartFty_0.94';


#===========================================================================================
# 기본 모듈 사용하기
#===========================================================================================
import time
from machine import Pin, time_pulse_us
from ETboard.lib.pin_define import *                     # ETboard 핀 관련 모듈
from ETboard.lib.servo import Servo


#===========================================================================================
# IoT 프로그램 사용하기
#===========================================================================================
from ET_IoT_App import ET_IoT_App, setup, loop
app = ET_IoT_App()


#===========================================================================================
# OLED 표시 장치 사용하기
#===========================================================================================
from ETboard.lib.OLED_U8G2 import *
oled = oled_u8g2()


#===========================================================================================
# 전역 변수 선언
#===========================================================================================
button_push = Pin(D7)                                    # 톱니바퀴 작동 버튼 핀 : D7

echo_pin = Pin(D8)                                       # 초음파 수신 핀: D8
trig_pin = Pin(D9)                                       # 초음파 송신 핀: D9

pump_state = 0                                           # 워터 펌프 상태: 멈춤

servo_block = Servo(Pin(D4))                             # 서보모터(차단대) 핀 : D4
servo_geer = Servo(Pin(D5))                              # 서보모터(차단대) 핀 : D5

count = 0                                                # 지나간 물건 개수
pre_time = 0                                             # 물건이 지나간 시간

distance = 0                                             # 거리
pos = 0                                                  # 컨베이어 위치 상태
block_state = 'close'                                    # 차단대 상태


#===========================================================================================
def et_setup():                                          #  사용자 맞춤형 설정
#===========================================================================================
    button_push.init(Pin.IN)                             # 밀기 버튼 : 입력 모드

    echo_pin.init(Pin.IN)                                # 초음파 수신부: 입력 모드
    trig_pin.init(Pin.OUT)                               # 초음파 송신부: 출력 모드

    initializing_process()                               # 초기화

    recv_message()


#===========================================================================================
def et_loop():                                           # 사용자 반복 처리
#===========================================================================================
    do_sensing_process()                                 # 센싱 처리
    do_automatic_process()                               # 자동화 처리


#===========================================================================================
def initializing_process():                              # 센싱 처리
#===========================================================================================
    global count, pos, block_state

    count = 0
    pos = 0
    block_state = 'close'

    servo_geer.write_angle(150)
    servo_block.write_angle(0)

    display_information()

    app.send_data('drum', 'count', count)
    app.send_data('block', 'state', block_state)
    app.send_data('pos', 'state', pos)


#===========================================================================================
def do_geer_process():                                   # 차단대 작동 처리
#===========================================================================================
    global pos

    if pos > 3:
        pos = 0

    app.send_data('pos', 'state', pos)

    if pos == 1:
        servo_geer.write_angle(103)
    elif pos == 2:
        servo_geer.write_angle(66)
    elif pos == 3:
        servo_geer.write_angle(26)
    else:
        servo_geer.write_angle(150)


#===========================================================================================
def do_sensing_process():                                # 센싱 처리
#===========================================================================================
    global pos, distance

    if button_push.value() == LOW:
        while True:
            if button_push.value() == HIGH:
                break
        pos += 1
        do_geer_process()

    # 초음파 송신
    trig_pin.value(LOW)
    echo_pin.value(LOW)
    time.sleep_ms(2)
    trig_pin.value(HIGH)
    time.sleep_ms(10)
    trig_pin.value(LOW)

    duration = time_pulse_us(echo_pin, HIGH)             # 초음파 수신까지의 시간 계산
    distance = 17 * duration / 1000                      # 거리 계산

    time.sleep(0.1)


#===========================================================================================
def do_automatic_process():                              # 자동화 처리
#===========================================================================================
    global distance, count, block_state, pre_time

    if distance > 2 and distance < 8:
        now = int(round(time.time() * 1000))
        if now - pre_time > 500:
            pre_time = now
            count += 1
            app.send_data('drum', 'count', count)

            time.sleep(0.5)

            servo_block.write_angle(75)
            block_state = 'open'
            app.send_data('block', 'state', block_state)
            time.sleep(1)
            servo_block.write_angle(0)
            block_state = 'close'
            app.send_data('block', 'state', block_state)


#===========================================================================================
def et_short_periodic_process():                         # 사용자 주기적 처리 (예 : 1초마다)
#===========================================================================================
    # 2024.10.12 : SCS : aws test
    global count 
    count = count + 1
    display_information()


#===========================================================================================
def et_long_periodic_process():                          # 사용자 주기적 처리 (예 : 5초마다)
#===========================================================================================
    send_message()


#===========================================================================================
def display_information():                               # OLED 표시
#===========================================================================================
    global board_firmware_version, count, pos

    string_count = "%d" % count
    string_pos = "%d" % pos

    oled.clear()
    oled.setLine(1, board_firmware_version)
    oled.setLine(2, 'count: ' + string_count)
    oled.setLine(3, 'pos: ' + string_pos)
    oled.display()


#===========================================================================================
def send_message():                                      # 메시지 송신
#===========================================================================================
    global count, pos, block_state

    app.send_data('drum', 'count', count)
    app.send_data('pos', 'state', pos)
    app.send_data('block', 'state', block_state)


#===========================================================================================
def recv_message():                                      # 메시지 수신
#===========================================================================================
    # 'pos' 메시지를 받으면 process_geer_control() 실행
    app.setup_recv_message('pos', process_geer_control)

    # 'block' 메시지를 받으면 process_block_control() 실행
    app.setup_recv_message('block', process_block_control)

    # 'reset' 메시지를 받으면 process_geer_control() 실행
    app.setup_recv_message('reset', process_reset_control)


#===========================================================================================
def process_geer_control(topic, msg):                    # 톱니바퀴(서보) 제어 처리
#===========================================================================================
    global pos
    pos = int(msg)
    do_geer_process()


#===========================================================================================
def process_block_control(topic, msg):                   # 차단대 제어 처리
#===========================================================================================
    global block_state

    if msg == 'open':
        servo_block.write_angle(75)
        block_state = 'open'
        print('차단대: 열림')
    else:
        servo_block.write_angle(0)
        block_state = 'close'
        print('차단대: 닫힘')

    app.send_data('block', 'state', block_state)


#===========================================================================================
def process_reset_control(topic, msg):                   # 리셋 처리
#===========================================================================================
    if msg == 'reset':
        initializing_process()


#===========================================================================================
# 시작 지점                     
#===========================================================================================
if __name__ == "__main__":
    setup(app, et_setup)
    while True:
        loop(app, et_loop, et_short_periodic_process, et_long_periodic_process)                                                                       