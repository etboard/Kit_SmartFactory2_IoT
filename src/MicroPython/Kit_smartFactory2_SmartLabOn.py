# ******************************************************************************************
# FileName     : Kit_smartFactory2_SmartLabOn.py
# Description  :
# Author       : 박은정
# Created Date : 2025.08.11 : PEJ
# Reference    :
# Modified     : 
# ******************************************************************************************
board_firmware_version = 'smartFty_0.91';


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

    do_geer_process()
    servo_block.write_angle(0)

    display_information()

    app.send_data('drum', 'count', count)
    app.send_data('block', 'state', block_state)
    app.send_data('pos', 'state', pos)


#===========================================================================================
def do_geer_process():                                   # 차단대 작동 처리
#===========================================================================================
    global pos

    if pos > 3:                                          # pos가 3보다 크다면
        pos = 0                                          # pos를 0으로 변경

    app.send_data('pos', 'state', pos)

    p = [180, 138, 102, 64]                               # 각도 저장

    servo_geer.write_angle(p[pos])                        # 톱니바퀴를 최종 각도로 설정


#===========================================================================================
def do_sensing_process():                                # 센싱 처리
#===========================================================================================
    global pos, distance

    if button_push.value() == LOW:                       # 드럼통 출고 버튼이 눌렸다면
        while True:
            if button_push.value() == HIGH:
                break
        pos += 1                                         # 톱니바퀴 작동
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

    if distance > 2 and distance < 8:                    # 측정된 거리가 2 초과 8 미만이라면
        now = int(round(time.time() * 1000))             # 현재 시간 저장
        if now - pre_time > 500:                         # 중복 카운트 방지
            pre_time = now
            count += 1                                   # 드럼통 출고 개수 증가
            app.send_data('drum', 'count', count)

            time.sleep(0.5)

            servo_block.write_angle(75)                  # 차단대 열기
            block_state = 'open'
            app.send_data('block', 'state', block_state)
            time.sleep(1)
            servo_block.write_angle(0)                   # 차단대 닫기
            block_state = 'close'
            app.send_data('block', 'state', block_state)


#===========================================================================================
def et_short_periodic_process():                         # 사용자 주기적 처리 (예 : 1초마다)
#===========================================================================================
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
    global distance, count

    app.add_sensor_data('distance', distance)
    app.add_sensor_data('count', count)
    app.send_sensor_data();


#===========================================================================================
def recv_message():                                      # 메시지 수신
#===========================================================================================
    # "get_sensor_type" 메시지를 받으면 send_sensor_type() 실행
    app.setup_recv_message('get_sensor_type', handle_get_sensor_type_request)


#===========================================================================================
def json_to_unicode_escaped(data):                       # 직렬화, 이스케이프
#===========================================================================================
    # JSON 직렬화
    json_string = ujson.dumps(data)

    # JSON 문자열에서 비-ASCII 문자를 Unicode 이스케이프 형식으로 변환
    return ''.join(f'\\u{ord(c):04x}' if ord(c) > 127 else c for c in json_string)


#===========================================================================================
def handle_get_sensor_type_request(topic, msg):          # 센서 타입 송신 처리
#===========================================================================================
    send_sensor_type()


#===========================================================================================
def send_sensor_type():                                  # 센서 타입 전송
#===========================================================================================
    sensor_type = {
        "sensorId": "distance",
        "sensorType": "distance",
        "sensorNicNm": "거리",
        "channelCode": "01",
        "collectUnit": "cm",
    }
    payload = json_to_unicode_escaped(sensor_type)
    app.send_data("sensor_types", "distance", payload)

    sensor_type = {
        "sensorId": "count",
        "sensorType": "count",
        "sensorNicNm": "드럼통 출고 수",
        "channelCode": "01",
        "collectUnit": "",
    }
    payload = json_to_unicode_escaped(sensor_type)
    app.send_data("sensor_types", "count", payload)


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


#===========================================================================================
#                                                    
# (주)한국공학기술연구원 http://et.ketri.re.kr       
#
#===========================================================================================