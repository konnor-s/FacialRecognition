#include <ArduinoBLE.h>
#include "TimeoutTimer.h"
#define BUFSIZE 20

/*   We'll use the ArduinoBLE library to simulate a basic UART connection 
 *   following this UART service specification by Nordic Semiconductors. 
 *   More: https://learn.adafruit.com/introducing-adafruit-ble-bluetooth-low-energy-friend/uart-service
 */
BLEService uartService("6E400001-B5A3-F393-E0A9-E50E24DCCA9E");
BLEStringCharacteristic txChar("6E400002-B5A3-F393-E0A9-E50E24DCCA9E", BLEWrite, 20 );
BLEStringCharacteristic rxChar("6E400003-B5A3-F393-E0A9-E50E24DCCA9E", BLERead | BLENotify, 20 );

void setup() 
{
  Serial.begin(9600);
  pinMode(6, INPUT_PULLUP);
  while(!Serial);

  if ( !BLE.begin() )
  {
    Serial.println("Starting BLE failed!");
    while(1);
  }

  // Get the Arduino's BT address
  String deviceAddress = BLE.address();

  // The device name we'll advertise with.
  BLE.setLocalName("ArduinoBLE UART");

  // Set the service and the service's characteristics
  BLE.setAdvertisedService( uartService );
  uartService.addCharacteristic( txChar );
  uartService.addCharacteristic( rxChar );
  BLE.addService( uartService );

  // Start advertising our new service.
  BLE.advertise();
  Serial.println("Bluetooth device (" + deviceAddress + ") active, waiting for connections...");
}

void loop() 
{
  // Wait for a BLE central device.
  BLEDevice central = BLE.central();

  // If a central device is connected to the peripheral...
  if ( central )
  {
    // Print the central's BT address.
    Serial.print("Connected to central: ");
    Serial.println( central.address() );

    // While the central device is connected...
    while( central.connected() )
    {
      // Get input from user, send to central
      char inputs[BUFSIZE+1] = "open";
      
      if ( digitalRead(6)== LOW )
      {
        Serial.print("[Send] ");
        Serial.println( inputs );
        rxChar.writeValue( inputs );
        delay(5000);
        while (digitalRead(6)== LOW){
        }
        Serial.print("closed");
      }

      // Receive data from central (if written is true)
      if ( txChar.written() )
      {
        Serial.print("[Recv] ");
        Serial.println( txChar.value() );
      }
    }
    
    Serial.print("Disconnected from central: ");
    Serial.println( central.address() );
    
  }
}

/**************************************************************************/
/*!
    @brief  Checks for user input (via the Serial Monitor)
            From: https://github.com/adafruit/Adafruit_BluefruitLE_nRF51
*/
/**************************************************************************/
bool getUserInput(char buffer[], uint8_t maxSize)
{
  // timeout in 100 milliseconds
  TimeoutTimer timeout(100);

  memset(buffer, 0, maxSize);
  while( (!Serial.available()) && !timeout.expired() ) { delay(1); }

  if ( timeout.expired() ) return false;

  delay(2);
  uint8_t count=0;
  do
  {
    count += Serial.readBytes(buffer+count, maxSize);
    delay(2);
  } while( (count < maxSize) && (Serial.available()) );
  
  return true;
}
