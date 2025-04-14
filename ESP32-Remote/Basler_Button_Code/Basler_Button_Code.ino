#include <ezButton.h>

// Declare instances of ezButton for each button
ezButton button1(12);  //Up +100
ezButton button2(11);  //Up +10
ezButton button3(10);  //Down -10
ezButton button4(5);   //Down -100
ezButton button5(6);   //Video
ezButton button6(9);   //Picture

ezButton button7(13);   //LED lights

// Define the pin for the button
//const int buttonPin = 13; // Change this to the pin number where your button is connected

// Define the pins for the LEDs
const int ledPin1 = A1; //13; // Change this to the pin number for your first LED
const int ledPin2 = A2; //12; // Change this to the pin number for your second LED
const int ledPin3 = A3; //11; // Change this to the pin number for your third LED
const int ledPin4 = A4; //10; // Change this to the pin number for your fourth LED

// Variable to store the current LED number
int currentLed = 1;

// Variable to store the previous state of the button
int previousButtonState = HIGH;

void setup() {
  Serial.begin(9600);

  // Set debounce time for buttons
  button1.setDebounceTime(50);
  button2.setDebounceTime(50);
  button3.setDebounceTime(50);
  button4.setDebounceTime(50);
  button5.setDebounceTime(50);
  button6.setDebounceTime(50);

  button7.setDebounceTime(50);

  // Initialize the LED pins as outputs
  pinMode(ledPin1, OUTPUT);
  pinMode(ledPin2, OUTPUT);
  pinMode(ledPin3, OUTPUT);
  pinMode(ledPin4, OUTPUT);

  // Initialize the button pin as an input with the internal pull-up resistor enabled
  //pinMode(button7, INPUT_PULLUP);
  currentLed = 0;
}

void loop() {
  // Read the state of the button
  //int buttonState = digitalRead(buttonPin);

  button7.loop();
  int buttonState = button7.getState();

  // Check if the button state has changed from HIGH to LOW (button is pressed)
  if (buttonState == LOW && previousButtonState == HIGH) {
    // Increment the current LED number
    currentLed++;

    // Wrap around to the first LED if the current LED number exceeds 5
    if (currentLed > 6) {
      currentLed = 1;
    }

    // Turn off all LEDs
    digitalWrite(ledPin1, LOW);
    digitalWrite(ledPin2, LOW);
    digitalWrite(ledPin3, LOW);
    digitalWrite(ledPin4, LOW);

    // Turn on the selected LED(s) based on the current LED number
    switch (currentLed) {
      case 1:
        digitalWrite(ledPin1, HIGH);
        break;
      case 2:
        digitalWrite(ledPin2, HIGH);
        break;
      case 3:
        digitalWrite(ledPin3, HIGH);
        break;
      case 4:
        digitalWrite(ledPin4, HIGH);
        break;
      case 5:
        digitalWrite(ledPin1, HIGH);
        digitalWrite(ledPin2, HIGH);
        digitalWrite(ledPin3, HIGH);
        digitalWrite(ledPin4, HIGH);
        break;
      case 6:
        digitalWrite(ledPin1, LOW);
        digitalWrite(ledPin2, LOW);
        digitalWrite(ledPin3, LOW);
        digitalWrite(ledPin4, LOW);
        break;
    }
  }

  // Store the current button state for comparison in the next iteration
  previousButtonState = buttonState;

  // Update button states
  button1.loop();
  button2.loop();
  button3.loop();
  button4.loop();
  button5.loop();
  button6.loop();

  // Check if each button is pressed or released and send corresponding message
  if (button1.isPressed()) {
    Serial.print("move: ");
    Serial.println("1");
  }

  if (button2.isPressed()) {
    Serial.print("move: ");
    Serial.println("2");
  }

  if (button3.isPressed()) {
    Serial.print("move: ");
    Serial.println("3");
  }

  if (button4.isPressed()) {
    Serial.print("move: ");
    Serial.println("4");
  }

  if (button5.isPressed()) {
    Serial.print("move: ");
    Serial.println("5");
  }

  if (button6.isPressed()) {
    Serial.print("move: ");
    Serial.println("6");
  }
}
