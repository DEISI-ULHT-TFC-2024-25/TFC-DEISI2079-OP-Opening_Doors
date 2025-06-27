#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <Servo.h>

const char* ssid = "LITO";
const char* password = "4W1DXZ34YA";

ESP8266WebServer server(80);

const int RELAY_PIN = 4;  // Pino que controla o relé (alimentação do servo)
const int SERVO_PIN = 14; // Pino do sinal do servo

Servo myservo;

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW); // relé desligado (servo sem alimentação)

  myservo.attach(SERVO_PIN);
  myservo.write(0); // posição inicial

  WiFi.begin(ssid, password);
  Serial.println("A conectar-se à rede WiFi...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi conectado");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());

  server.on("/toggle", HTTP_GET, []() {
  static bool ligado = false;
  ligado = !ligado;

  digitalWrite(RELAY_PIN, HIGH);  // Liga alimentação em qualquer caso
  delay(50);                      // Espera alimentação estabilizar

  if (ligado) {
    myservo.write(180);           // Porta abre
  } else {
    myservo.write(0);            // Porta fecha
  }

  delay(500);                     // Espera servo completar movimento

  if (!ligado) {
    digitalWrite(RELAY_PIN, LOW); // Só corta a alimentação ao fechar
  }

  server.send(200, "text/plain", ligado ? "Porta aberta via relé" : "Porta fechada via relé");
});


  server.begin();
  Serial.println("Servidor HTTP iniciado.");
}

void loop() {
  server.handleClient();
}
