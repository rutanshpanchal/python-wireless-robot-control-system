#include <WiFi.h>

const char* ssid = "vivo V60e";
const char* password = "9106038009";

WiFiServer server(80);

// Motor pins
int IN1 = 5;
int IN2 = 18;
int IN3 = 19;
int IN4 = 21;

void setup() {
  Serial.begin(115200);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  WiFi.begin(ssid, password);

  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  server.begin();
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("Client Connected");

    // Wait until data is available
    while (!client.available()) {
      delay(1);
    }

    // Read first line of request
    String request = client.readStringUntil('\n');
    Serial.println(request);

    // Send response
    client.println("HTTP/1.1 200 OK");
    client.println("Content-type:text/html");
    client.println();
    client.println("OK");

    // COMMAND CHECK (VERY IMPORTANT)
    if (request.indexOf("GET /F") != -1) {
      Serial.println("FORWARD");
      forward();
    }
    else if (request.indexOf("GET /B") != -1) {
      Serial.println("BACKWARD");
      backward();
    }
    else if (request.indexOf("GET /L") != -1) {
      Serial.println("LEFT");
      left();
    }
    else if (request.indexOf("GET /R") != -1) {
      Serial.println("RIGHT");
      right();
    }
    else if (request.indexOf("GET /S") != -1) {
      Serial.println("STOP");
      stopCar();
    }

    delay(1);
    client.stop();
    Serial.println("Client Disconnected");
  }
}

void forward() {
  Serial.println("FORWARD");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void backward() {
  Serial.println("BACKWARD");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void left() {
  Serial.println("LEFT");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void right() {
  Serial.println("RIGHT");
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopCar() {
  Serial.println("STOP");
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}
