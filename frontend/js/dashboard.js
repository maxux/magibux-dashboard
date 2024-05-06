function zlead(x) {
    return (x < 10) ? "0" + x : x;
}

Date.prototype.today = function() {
    return this.getFullYear() + "-" + zlead(this.getMonth() + 1) + "-" + zlead(this.getDate());
}

Date.prototype.timeNow = function() {
     return zlead(this.getHours()) + ":" + zlead(this.getMinutes()) + ":" + zlead(this.getSeconds());
}

Date.prototype.dayName = function() {
    return this.toLocaleDateString("en-US", {weekday: 'long'});
}

function update_time() {
    var now = new Date();

    $('#current-time').html(now.timeNow());
    $('#current-date').html(now.today());
    $('#current-day').html(now.dayName());
}

var socket;

function connect() {
    socket = new WebSocket("ws://" + window.location.hostname + ":30900/");

    socket.onopen = function() {
        console.log("websocket open");
        $('#disconnected').hide();
    }

    socket.onmessage = function(msg) {
        json = JSON.parse(msg.data);
        console.log(json);

        switch(json['type']) {
            case "temperature":
                var values = json['payload'];
                for(var index in values) {
                    $(".temperature-" + index).html(values[index].toFixed(1) + "°C");
                }
            break;

            case "pressure":
                var values = json['payload'];
                for(var index in values) {
                    $(".pressure-" + index).html(values[index].toFixed(1) + " bar");
                }
            break;

            case "location":
                let location = json['payload'];

                $("h2#speed .val").html(location['speed'].toFixed(2));

                let lat = location['coord']['lat'].toFixed(6);
                let lng = location['coord']['lng'].toFixed(6);
                let place = location['place'];

                $("#coord").html(lat + ", " + lng);
                $("#locality").html(place[0] + ", " + place[1]);
                $("#country").html(place[3]);

                $("#trip .val").html(location['trip'].toFixed(2));

                update_map(location['coord']['lat'], location['coord']['lng']);
            break;

            default:
                console.log("Unknown type");
                console.log(json);
        }
    }

    socket.onclose = function() {
        $('#disconnected').show();
        setTimeout(connect, 2000);
    }
}


$(document).ready(function() {
    setInterval(update_time, 1000);
    update_time();

    connect();
});


var map = null;
var marker = null;
var socket = null;

function update_map(lat, lng) {
    let coord = {lat: lat, lng: lng};

    // cleanup previous marker
    if(marker)
        marker.setMap(null);

    // update new marker
    marker = new google.maps.Marker({
        position: coord,
        map: map,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 5
        },
        title: 'Location'
    });

    map.setCenter(coord);
}


/*
function tracker(data) {
    var trip = live(data);

    if(marker)
        marker.setMap(null);

    marker = new google.maps.Marker({
        position: trip['coord'],
        map: map,
        icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 5
          },
        title: 'Current position'
    });

    var speed = trip['speed'].toFixed(0)
    var speedtext = speed + ' km/h';

    console.log(trip);

    var signal = "Searching...";
    if(trip['quality'] == "GPS")
        var signal = trip['quality'] + " (Satellites: " + trip['sats'] + ", HDOP: " + trip['hdop'] + ")";

    var livetitle = 'Live session';
    var liveclass = 'text-success';

    if(trip['status'] == 'offline') {
        var livetitle = "Tracker offline";
        var liveclass = 'text-danger';
    }

    $('.live-title').attr('class', liveclass).html(livetitle);
    $('.trip-signal').html(signal);
    $('.trip-updated').html(trip['update']);
    $('.trip-now-speed').html(speedtext);

    if(trip['coord']['lat'])
        map.setCenter(trip['coord']);
}
*/

function initMap() {
    map = new google.maps.Map(document.getElementById('map'), {
        zoom: 14,
        center: {lat: 50.639827, lng: 5.568498},
        mapTypeId: 'terrain',
        disableDefaultUI: true,
        styles: [
            { elementType: "geometry", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.stroke", stylers: [{ color: "#242f3e" }] },
            { elementType: "labels.text.fill", stylers: [{ color: "#746855" }] },
            {
              featureType: "administrative.locality",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "poi",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "poi.park",
              elementType: "geometry",
              stylers: [{ color: "#263c3f" }],
            },
            {
              featureType: "poi.park",
              elementType: "labels.text.fill",
              stylers: [{ color: "#6b9a76" }],
            },
            {
              featureType: "road",
              elementType: "geometry",
              stylers: [{ color: "#38414e" }],
            },
            {
              featureType: "road",
              elementType: "geometry.stroke",
              stylers: [{ color: "#212a37" }],
            },
            {
              featureType: "road",
              elementType: "labels.text.fill",
              stylers: [{ color: "#9ca5b3" }],
            },
            {
              featureType: "road.highway",
              elementType: "geometry",
              stylers: [{ color: "#746855" }],
            },
            {
              featureType: "road.highway",
              elementType: "geometry.stroke",
              stylers: [{ color: "#1f2835" }],
            },
            {
              featureType: "road.highway",
              elementType: "labels.text.fill",
              stylers: [{ color: "#f3d19c" }],
            },
            {
              featureType: "transit",
              elementType: "geometry",
              stylers: [{ color: "#2f3948" }],
            },
            {
              featureType: "transit.station",
              elementType: "labels.text.fill",
              stylers: [{ color: "#d59563" }],
            },
            {
              featureType: "water",
              elementType: "geometry",
              stylers: [{ color: "#17263c" }],
            },
            {
              featureType: "water",
              elementType: "labels.text.fill",
              stylers: [{ color: "#515c6d" }],
            },
            {
              featureType: "water",
              elementType: "labels.text.stroke",
              stylers: [{ color: "#17263c" }],
            },
        ],
    });
}
