#include <Wire.h>
#include <BH1750.h> 
#include <DHT.h> 

#define DHT11_PIN 2 // Digital pin for DHT11 sensor
#define DHTTYPE DHT11 // Using DHT11 model
#define SOIL_PIN A0 // Analog pin the soil moisture sensor

BH1750 lightMeter; // Create the light sensor object
DHT dht(DHT11_PIN, DHTTYPE); // Create the DHT sensor object with pin/type parameters

void setup() {
  Serial.begin(9600); 
  Wire.begin(); // Start the I2C bus for the light sensor
  lightMeter.begin(); // Initialize the light sensor
  dht.begin(); // Initialize the DHT sensor
  Serial.println("Sensor test starting..."); 
  delay(1000); // Small delay before first reading
}

void loop() {
  // Soil moisture (analog)
  int soilValue = analogRead(SOIL_PIN); // Read raw analog value (0-1023) from the soil sensor

  // Light sensor (I2C)
  float lux = lightMeter.readLightLevel(); // Read ambient light level in lux

  // Temp/humidity (digital)
  float humidity = dht.readHumidity(); // Read humidity percentage from the DHT11
  float temperature = dht.readTemperature(); // Read temperature in Celsius from the DHT11

  // Print all three
  Serial.print("Soil: ");
  Serial.print(soilValue); // Output soil reading
  Serial.print(" | Lux: ");
  Serial.print(lux); // Output light reading
  Serial.print(" | Temp: ");
  if (isnan(temperature)) { // Check for DHT11 failing
    Serial.print("FAILED"); // Flag a bad temperature read 
  } else {
    Serial.print(temperature);
    Serial.print("C");
  }
  Serial.print(" | Humidity: ");
  if (isnan(humidity)) { // Same failure check for humidity
    Serial.println("FAILED"); 
  } else {
    Serial.print(humidity);
    Serial.println("%");          
  }

  delay(2000); // Delay between reads
}