var firebase = require('firebase/app');
var nodeimu = require('@trbll/nodeimu');
var IMU = new nodeimu.IMU();
var sense = require('@trbll/sense-hat-led');
const { getDatabase, ref, onValue, set, update, get, child } = require('firebase/database');
const { createBluetooth } = require( 'node-ble' );

const ARDUINO_BLUETOOTH_ADDR = '95:34:6d:ae:85:35';

const UART_SERVICE_UUID      = '6E400001-B5A3-F393-E0A9-E50E24DCCA9E';
const TX_CHARACTERISTIC_UUID = '6E400002-B5A3-F393-E0A9-E50E24DCCA9E';
const RX_CHARACTERISTIC_UUID = '6E400003-B5A3-F393-E0A9-E50E24DCCA9E';

const ESS_SERVICE_UUID       = '0000181a-0000-1000-8000-00805f9b34fb';
const TEMP_CHAR_UUID         = '00002a6e-0000-1000-8000-00805f9b34fb';

var light_col = 2;
var light_row = 0;
var light_r = 255;
var light_g = 0;
var light_b = 0;
var humidity = 0;
var temperature = 0;
var interval = 1;

const firebaseConfig = {
    apiKey: "AIzaSyBW98TK2hIIszUBc40ndoUTnz1CAU_ypJ0",
    authDomain: "lab2-b5abd.firebaseapp.com",
    projectId: "lab2-b5abd",
    storageBucket: "lab2-b5abd.appspot.com",
    messagingSenderId: "1054650953512",
    appId: "1:1054650953512:web:4663ee3b55f8995a1a2a1d",
    measurementId: "G-LG79614Z0N"
};
firebase.initializeApp(firebaseConfig);
const database = getDatabase();
const dbRef = ref(database);


async function main( )
{
    // Reference the BLE adapter and begin device discovery...
    const { bluetooth, destroy } = createBluetooth();
    const adapter = await bluetooth.defaultAdapter();
    try{
      const discovery =  await adapter.startDiscovery();  
    }catch{
        
    }
    
    console.log( 'discovering...' );

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
    // Get references to the desired ESS service and its temparature characteristic.
    const essService = await gattServer.getPrimaryService( ESS_SERVICE_UUID );
    const tempChar = await essService.getCharacteristic( TEMP_CHAR_UUID );
   
    
    // Register for notifications on the RX characteristic
    await rxChar.startNotifications( );

    // Callback for when data is received on RX characteristic
    rxChar.on( 'valuechanged', buffer =>
    {
        console.log('Received: ' + buffer.toString());
    });

    // Register for notifications on the temperature characteristic
    await tempChar.startNotifications();

    // Callback for when data is received on the temp characteristic
    tempChar.on( 'valuechanged', buffer =>
    {
        temperature = buffer[1] << 8 | buffer[0];
        temperature = temperature * .01;

    });
    var interv = setInterval(sendTemp, interval*1000);
    const update_light = ref(database, 'update_light');
    onValue(update_light, (snapshot) => {
    const data = snapshot.val();
    if (data == true) {
        getColors();
        
    }
});
    // Set up listener for console input.
    // When console input is received, write it to TX characteristic
    const stdin = process.openStdin( );
    stdin.addListener( 'data', async function( d )
    {
        let inStr = d.toString( ).trim( );

        // Disconnect and exit if user types 'exit'
        if (inStr === 'exit')
        {
            console.log( 'disconnecting...' );
            await device.disconnect();
            console.log( 'disconnected.' );
            destroy();
            process.exit();
        }

        // Specification limits packets to 20 bytes; truncate string if too long.
        inStr = (inStr.length > 20) ? inStr.slice(0,20) : inStr;

        // Attempt to write/send value to TX characteristic
        await txChar.writeValue(Buffer.from(inStr)).then(() =>
        {
            console.log('Sent: ' + inStr);
        });
    });
    const temp_interval = ref(database, 'interval');
    onValue(temp_interval, (snapshot) => {
        const data = snapshot.val();
        interval = data;
        clearInterval(interv);
        interv = setInterval(sendTemp, interval*1000);
        console.log("here");
        // Attempt to write/send value to TX characteristic
        txChar.writeValue(Buffer.from(interval.toString())).then(() =>
        {
            console.log('New Interval: ' + interval);
        });
    });
    
    function getColors() {
        console.log("getColors");
        get(child(dbRef, 'light_col')).then((snapshot) => {
    
            light_col = snapshot.val();
            get(child(dbRef, 'light_row')).then((snapshot) => {
                light_row = snapshot.val();
                get(child(dbRef, 'light_r')).then((snapshot) => {
                    light_r = snapshot.val();
                    get(child(dbRef, 'light_g')).then((snapshot) => {
                        light_g = snapshot.val();
                        get(child(dbRef, 'light_b')).then((snapshot) => {
                            light_b = snapshot.val();
                            get(child(dbRef, 'light_b')).then((snapshot) => {
                                light_b = snapshot.val();
                                writePixel();
                                console.log(light_row + ", " + light_col + " [" + light_r + ", " + light_g + ", " + light_b + "]");
                            });
                        });
    
                    });
    
                });
    
            });
    
        });
    
    }
    function writePixel() {
        sense.setPixel(light_col, light_row, [light_r, light_g, light_b], (err) => {
            sense.getPixel(light_row, light_col, (err, color) => {
            })
        })
    }
    function sendTemp(){
        IMU.getValue((err,data) => {
            if (err !== null){
                console.error("couldn't read sensors");
            }
            humidity = data.humidity;
        });
        update(dbRef, {temperature: temperature, humidity: humidity});
        console.log("Temp: " + temperature + "\nHumidity: " + humidity);
    }
}






main().then((ret) =>
{
    if (ret) console.log( ret );
}).catch((err) =>
{
    if (err) console.error( err );
});