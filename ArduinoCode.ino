bool ledState = LOW;

void setup() {
  Serial.begin(9600);
  delay(2000);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, ledState);
}

void loop() {
  if (Serial.available()) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();

    if (comando == "ON") {
      ledState = HIGH;
      Serial.println("LED ligado!");
    } else if (comando == "OFF") {
      ledState = LOW;
      Serial.println("LED desligado!");
    } else {
      Serial.println("Comando inválido.");
    }
  }


  digitalWrite(LED_BUILTIN, ledState);
}
