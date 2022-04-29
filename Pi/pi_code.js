var admin = require("firebase-admin");
const { initializeApp, cert } = require('firebase-admin/app');
const { getStorage } = require('firebase-admin/storage');

const PiCamera = require('pi-camera');
var firebase = require('firebase/app');
var nodeimu = require('@trbll/nodeimu');
const { getDatabase, ref, onValue, set, update, get, child } = require('firebase/database');
const { createBluetooth } = require( 'node-ble' );

const ARDUINO_BLUETOOTH_ADDR = '95:34:6d:ae:85:35';

const UART_SERVICE_UUID      = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
const TX_CHARACTERISTIC_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E';
const RX_CHARACTERISTIC_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E';

var serviceAccount = require("/home/pi/lab2/serviceAccountKey.json");

admin.initializeApp({
  credential: admin.credential.cert(serviceAccount),
  storageBucket: 'gs://iotproject-60e4c.appspot.com' 
});

const bucket = getStorage().bucket();


const options = {
    destination: 'Unchecked/image.png',
   
  };

async function main( )
{
    // Reference the BLE adapter and begin device discovery...
    const { bluetooth, destroy } = createBluetooth();
    const adapter = await bluetooth.defaultAdapter();
   
    if (!await adapter.isDiscovering()){
        await adapter.startDiscovery();
        console.log('discovering...');
    }    

    // Attempt to connect to the device with specified BT address
    const device = await adapter.waitDevice( ARDUINO_BLUETOOTH_ADDR.toUpperCase() );
    console.log( 'found device. attempting connection...' );
    await device.connect();
    console.log( 'connected to device!' );

    // Get references to the desired UART service and its characteristics
    const gattServer = await device.gatt(); 
    
    const uartService = await gattServer.getPrimaryService( UART_SERVICE_UUID.toLowerCase() );
    const txChar = await uartService.getCharacteristic( TX_CHARACTERISTIC_UUID.toLowerCase() );
    const rxChar = await uartService.getCharacteristic( RX_CHARACTERISTIC_UUID.toLowerCase() );
  
    const myCamera = new PiCamera({
        mode: 'photo',
        output: "~/Desktop/a.jpg",
        width: 640,
        height: 480,
        nopreview: true,
      });
    
    // Register for notifications on the RX characteristic
    await rxChar.startNotifications( );

    // Callback for when data is received on RX characteristic
    rxChar.on( 'valuechanged', buffer =>
    {
        if (buffer.toString() == "OPEN"){
            myCamera.snap().then((result) => {
                console.log("picture taken");
                imageToUpload = bucket.upload("/home/pi/Desktop/a.jpg", options);
                console.log("image uploaded");
            // Your picture was captured
            })
            .catch((error) => {
            console.log(error);
            });
            
        } 
    });
        
}

main().then((ret) =>
{
    if (ret) console.log( ret );
}).catch((err) =>
{
    if (err) console.error( err );
});