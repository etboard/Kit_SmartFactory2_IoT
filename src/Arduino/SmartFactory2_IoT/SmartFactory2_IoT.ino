 /******************************************************************************************
 * FileName     : SmartFactory2_IoT.ino
 * Description  : 이티보드 스마트 팩토리2 코딩 키트(IoT)
 * Author       : SCS
 * Created Date : 2023.11.09
 * Reference    : 
 * Modified     : 2024.09.10 : PEJ : 프로그램 구조 변경
******************************************************************************************/
const char* board_firmware_verion = "smartFty_0.93";


//==========================================================================================
// IoT 프로그램 사용하기
//==========================================================================================
#include "ET_IoT_App.h"
ET_IoT_App app;


//==========================================================================================
// 서보 모터 사용하기
//==========================================================================================
#include <Servo.h>
Servo servo_block;
Servo servo_geer;


//==========================================================================================
// 전역 변수 선언
//==========================================================================================
const int button_push = D7;                              // 톱니바퀴 작동 버튼 핀 : D7

const int echo_pin = D8;                                 // 초음파 수신 핀: D8
const int trig_pin = D9;                                 // 초음파 송신 핀: D9

const int servo_block_pin = D4;                          // 서보 모터(차단대) 핀 : D4
const int servo_geer_pin = D5;                           // 서보 모터(톱니 바퀴) 핀 : D5

int count = 0;                                           // 지나간 물건 개수
int pos = 0;                                             // 컨베이어 위치 상태
String block_state = "close";                            // 차단대 상태

float distance;                                          // 거리
int pre_time = 0;                                        // 물건이 지나간 시간



//==========================================================================================
void et_setup()                                          // 사용자 맞춤형 설정
//==========================================================================================
{
  pinMode(trig_pin, OUTPUT);                             // 초음파 송신부: 출력 모드
  pinMode(echo_pin, INPUT);                              // 초음파 수신부: 입력 모드

  servo_block.attach(servo_block_pin);                   // 차단대 서보 모터 핀 설정
  servo_geer.attach(servo_geer_pin);                     // 톱니바퀴 서보 모터 핀 설정

  initializing_process();                                // 초기화
}


//==========================================================================================
void et_loop()                                           // 사용자 반복 처리
//==========================================================================================
{
  do_sensing_process();                                  // 센싱 처리

  do_automatic_process();                                // 자동화 처리
}


//==========================================================================================
void initializing_process()                              // 초기화
//==========================================================================================
{
  pos = 0;
  count = 0;
  block_state = "close";

  servo_geer.write(150);
  servo_block.write(0);

  display_information();

  app.send_data("pos", "state", pos);                    // 톱니바퀴 상태 응답
  app.send_data("drum", "count" ,count);                 // 드럼통 출고 개수 응답
  app.send_data("block", "state", block_state);          // 서보모터 상태 응답
}


//==========================================================================================
void do_geer_process()                                   // 서보모터 작동 처리
//==========================================================================================
{
  if (pos > 3) {
    pos = 0;
  }

  app.send_data("pos", "state", pos);                    // 톱니바퀴 상태 응답

  switch (pos) {
    case 1:
      servo_geer.write(100);
      break;
    case 2:
      servo_geer.write(56);
      break;
    case 3:
      servo_geer.write(28);
      break;
    default:
      servo_geer.write(150);
      break;
  }
}


//==========================================================================================
void do_sensing_process()                                // 센싱 처리
//==========================================================================================
{
  if (digitalRead(button_push) == LOW) {                 // 버튼이 눌렸다면
    while (true) {
      if (digitalRead(button_push) == HIGH) break;
    }
    pos++;                                               // 각도 증가
    do_geer_process();                                   // 톱니바퀴 작동
  }

  // 초음파 송신
  digitalWrite(trig_pin, LOW);
  digitalWrite(echo_pin, LOW);
  delayMicroseconds(2);
  digitalWrite(trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);

  unsigned long duration  = pulseIn(echo_pin, HIGH);     // 초음파 수신까지의 시간 계산
  distance = duration * 17 / 1000;                       // 거리 계산

  delay(100);
}


//==========================================================================================
void do_automatic_process()                              // 자동화 처리
//==========================================================================================
{
  if(distance > 2 && distance < 8) {                     // 거리가 2cm 초과 8cm 미만일 때
    int now = millis();                                  // 현재 시간 저장
    if (now - pre_time > 500) {                          // 현재 시간과 이전 시간 비교
      pre_time = now;                                    // 물건이 지나간 시간 업데이트
      count++;                                           // 지나간 물건 개수 증가
      app.send_data("drum", "count", count);             // 지나간 물건 개수 송신
      delay(500);

      servo_block.write(75);
      block_state = "open";
      app.send_data("block", "state", block_state);           // 차단대 상태 응답
      delay(1000);
      servo_block.write(0);
      block_state = "close";
      app.send_data("block", "state",  block_state);         // 차단대 상태 응답
    }
  }
}

//==========================================================================================
void et_short_periodic_process()                         // 사용자 주기적 처리 (예 : 1초마다)
//==========================================================================================
{
  display_information();                                 // 표시 처리
}


//==========================================================================================
void et_long_periodic_process()                          // 사용자 주기적 처리 (예 : 5초마다)
//==========================================================================================
{
  send_message();
}


//==========================================================================================
void display_information()                               // OLED 표시
//==========================================================================================
{
  String string_count = String(count);                   // 수분 값을 문자열로 변환
  String string_pos = String(pos);                       // 수분 값을 문자열로 변환

  app.oled.setLine(1, board_firmware_verion);            // 1번째 줄에 펌웨어 버전
  app.oled.setLine(2, "count : " + string_count);        // 2번재 줄에 개수
  app.oled.setLine(3, "pos : " + string_pos);            // 3번재 줄에 각도
  app.oled.display();                                    // OLED에 표시
}


//==========================================================================================
void send_message()                                      // 메시지 송신
//==========================================================================================
{
  app.send_data("pos", "state", pos);                    // 톱니바퀴 상태 응답
  app.send_data("drum", "count" ,count);                 // 드럼통 출고 개수 응답
  app.send_data("block", "state", block_state);          // 서보모터 상태 응답
}


//==========================================================================================
void recv_message()                                      // 메시지 수신
//==========================================================================================
{
  // "pos" 메시지를 받으면 process_geer_control() 실행
  app.setup_recv_message("pos", process_geer_control);

  // "block" 메시지를 받으면 process_block_control() 실행
  app.setup_recv_message("block", process_block_control);

  // "reset" 메시지를 받으면 process_reset_control() 실행
  app.setup_recv_message("reset", process_reset_control);
}


//==========================================================================================
void process_geer_control(const String &msg)             // 톱니바퀴(서보) 제어 처리
//==========================================================================================
{
  pos = msg.toInt();                                     // pos에 메시지 값 저장
  do_geer_process();
}


//==========================================================================================
void process_block_control(const String &msg)            // 차단대 제어 처리
//==========================================================================================
{
  if (msg == "open") {                                   // "open"이면
    servo_block.write(75);                               // 차단대 열기
    block_state = "open";
    Serial.println("차단대: 열림");
  } else {                                               // 그렇지 않으면
    servo_block.write(0);                                // 차단대 닫기
    block_state = "close";
    Serial.println("차단대: 닫힘");
  }
  app.send_data("block", "state", block_state);          // 차단대 작동 상태 응답
}


//==========================================================================================
void process_reset_control(const String &msg)            // 리셋 처리
//==========================================================================================
{
  if(msg == "reset") {
    initializing_process();
  }
}


//==========================================================================================
//                                                    
// (주)한국공학기술연구원 http://et.ketri.re.kr       
//                                                    
//==========================================================================================