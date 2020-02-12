// Metercap
// 1. Connect to your capture device
// 2. Start Web Service: python3 -m http.server --cgi 8000

var service_url0 = '/cgi-bin/cgiserial.py';
var meter1_id;
var meter1_energy_consumption;
var meter1_energy_production;
var meter1_power;
var meter2_id;
var meter2_energy_consumption;
var meter2_energy_production;
var meter2_power;

ready();

function ready() {
    if (document.readyState != 'loading'){
      start();
    } else {
      document.addEventListener('DOMContentLoaded', start);
    }
}

function start() {
    DataRequest(0);
}

function DataRequest(port) {
  var request = new XMLHttpRequest();
  var data_read_array = [];
  request.open('GET', service_url, true);
  request.addEventListener('load', function() {
      if (request.status >= 200 && request.status < 300) {
        // Verbindung erfolgreich
        data_read_array = request.responseText.split(/\r?\n/g);
        alert(request.responseText);
        ParseData(data_read_array);
        DataRequest(0);
      } else {
        // Fehler Statuscode Server
      }
  });
  request.onerror = function() {
  // Fehler Connection
  };
  request.send();
}

function ParseData(data_read_array) {
  var descriptor = '';
  var energy_consumption = null;
  var energy_production = null;
  var power = null;
  var meterclass = null;
  // Ausgelesene Zeilen parsen
  data_read_array.forEach(function(item, index, array) {
    descriptor = item.split('*')[0]
    if (descriptor == 'A+') { energy_consumption = item.split('*')[1] }
    if (descriptor == 'A-') { energy_production = item.split('*')[1] }
    if (descriptor == 'P') { power = item.split('*')[1] }
  })
  // DEBUGGG : ENTFERNEN!!!!
  power =  (Math.random() * (1000 - 1)) + 1;
  if (energy_consumption != null && energy_consumption > 8000) {
    energy_consumption = 123.12;
    energy_production = 9898.34;
  }

  // Datenzuordnung (1)Haupt- / (2)Erzeugungszaehler
  if (energy_consumption != null && energy_production != null && power != null) {
    if (energy_production == 0) {
      meterclass = 1; // Hauptzaehler
    } else if ((energy_consumption / energy_production) < 0.1 ) {
      meterclass = 2; // Erzeugungszaehler
    } else {
      meterclass = 1; // Hauptzaehler
    }
  }

  if (meterclass == 1) {
    meter1_id = 'Haupt';
    meter1_energy_consumption = energy_consumption;
    meter1_energy_production = energy_production;
    meter1_power = power;
    document.getElementById("meter1_energy_consumption").innerHTML = meter1_energy_consumption;
    document.getElementById("meter1_energy_production").innerHTML = meter1_energy_production;
    document.getElementById("meter1_power").innerHTML = meter1_power;
    UpdateStat();
  }

  if (meterclass == 2) {
    meter2_id = 'Erzeugung';
    meter2_energy_consumption = energy_consumption;
    meter2_energy_production = energy_production;
    meter2_power = power;
    document.getElementById("meter2_energy_consumption").innerHTML = meter2_energy_consumption;
    document.getElementById("meter2_energy_production").innerHTML = meter2_energy_production;
    document.getElementById("meter2_power").innerHTML = meter2_power;
    UpdateStat();
  }
}  

function UpdateStat() {
  var verbrauch; 
  var eigenverbrauch_quote = 0;
  var eigenbedarf_deckung = 0;
  verbrauch = meter1_power - meter2_power;
  if (meter2_power < 0) {
    eigenverbrauch_quote = (verbrauch / abs(meter2_power)) * 100;
    if (eigenverbrauch_quote > 100) { eigenverbrauch_quote = 100; }
    eigenbedarf_deckung = (abs(meter2_power) / verbrauch) * 100
    if (eigenbedarf_deckung > 100) { eigenbedarf_deckung = 100; }
  } else {
    eigenverbrauch_quote = 0;
    eigenbedarf_deckung = 0;
  }
}
