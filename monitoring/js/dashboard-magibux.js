var units  = ['b', 'KiB', 'MiB', 'GiB', 'TiB', 'PiB'];
var rates  = ['b/s', 'KiB/s', 'MiB/s', 'GiB/s', 'TiB/s', 'PiB/s'];
var shortrates  = ['b', 'K', 'M', 'G', 'T', 'P'];
var batpic = ["→", "↓", "↑"];

var color;
var root;

function elapsedstr(elapsed) {
    if(elapsed < 60)
        return elapsed + ' seconds ago';

    elapsed /= 60
    if(elapsed < 60)
        return elapsed.toFixed(0) + ' minutes ago';

    return (elapsed / 60).toFixed(0) + ' hours ago';
}

function elapsedvisibiliy(elapsed) {
    if(elapsed < 3600)
        return 'visibility-recent';

    if(elapsed < (3600 * 3))
        return 'visibility-middle';

    return 'visibility-old';
}

function percentstyle(percent) {
	return 'color: black;';
}

function percentvalue(value, total) {
	if(total == 0)
		return 0;

	return parseFloat(Math.floor((value / total) * 100));
}

function colorizesw(value, size) {
	if(value < 10)
		return {'class': 'text-muted'};

    if(value < 2)
		return {'class': 'text-muted'};

	if(value < 30)
		return {'class': 'text-info'};

	return colorize(value);
}

function colorize(value) {
	if(value < 8)
		return {'class': 'text-muted'};

    if(value < 18)
        return {'class': ''};

	if(value < 50)
		return {'class': 'text-info'};

	if(value < 80)
		return {'class': 'text-warning'};

	return {'class': 'text-danger'};
}

function loadcolor(value, cpu) {
	if(value < 0.8)
		return {'class': 'text-muted'};

    if(value < 1.5)
        return {'class': ''};

	if(value < cpu / 4)
		return {'class': 'text-info'};

	if(value < cpu)
		return {'class': 'text-warning'};

	return {'class': 'text-danger'};
}

function autosize(value) {
	var temp = value / 1024;
	var unitidx = 2;

	if(temp > 4096) {
		temp /= 1024;
		unitidx = 3;
	}

	return temp.toFixed(0) + ' ' + units[unitidx];
}

//
// return a value prefixed by zero if < 10
//
function zerolead(value) {
	return (value < 10) ? '0' + value : value;
}

//
// convert a unix timestamp to readable european date/hours
//
function unixtime(timestamp) {
	var date = new Date(timestamp * 1000);

	var hours = zerolead(date.getHours()) + ':' +
	            zerolead(date.getMinutes()) + ':' +
	            zerolead(date.getSeconds());

	return hours;
}

//
// compute a scaled size with adapted prefix
//
function size(value, total) {
	uindex = 1;

	pc = Math.floor((value / total) * 100);

	for(; value > 1024; value /= 1024)
		uindex++;

	text = value.toFixed(2) + ' ' + units[uindex] + (total ? ' (' + pc + ' %)' : '');

	return $('<span>', {style: percentstyle(pc)}).html(text);
}

function streamsize(value) {
	uindex = 0;

	for(; value > 1024; value /= 1024)
		uindex++;

	text = value.toFixed(2) + ' ' + units[uindex];

	pc = ((uindex / rates.length) * 100);

	return $('<span>', {style: percentstyle(pc)}).html(text);
}

function rate(value) {
	value = value / 1024;
	uindex = 1;

	for(; value > 1024; value /= 1024)
		uindex++;

	// return value.toFixed(2).padStart(4,'&nbsp;') + ' ' + rates[uindex];
	return value.toFixed(0) + ' ' + rates[uindex];
}

function shortrate(value) {
	value = value / 1024;
	uindex = 1;

	for(; value > 1024; value /= 1024)
		uindex++;

	return value.toFixed(2) + ' ' + shortrates[uindex];
}

function colorintf(value, maxspeed) {
	var value = value / 1024 / 1024; // let's compute everything in Mbps

	// compute color based on interface speed/capacity
	// if scale is unknown, setting it to 100 Mbps
	if(maxspeed == 0)
		scale = 100;

	// computing percentage of usage
	var pc = (value / maxspeed) * 100;

	if(value < 0.5)
		return {'class': ''};

	if(value < 40)
		return {'class': 'text-info'};

	if(value < 60)
		return {'class': 'text-warning'};

	return {'class': 'text-danger'};
}

function colordisk(value) {
	// using MB/s
	value = value / 1024 / 1024;

	if(value < 1.2)
		return {'class': ''};

	if(value < 20)
		return {'class': 'text-info'};

	if(value < 100)
		return {'class': 'text-warning'};

	return {'class': 'text-danger'};
}

function colorcputemp(text, value) {
    if(value == 0)
        return $('<span>', {'class': 'text-muted'}).html(text);

    if(value < 45)
        return $('<span>', {'class': 'text-muted'}).html(text);

    if(value < 55)
        return $('<span>', {'class': ''}).html(text);

    if(value < 65)
        return $('<span>', {'class': 'text-warning'}).html(text);

    return $('<span>', {'class': 'text-danger'}).html(text);
}

function colorhddtemp(text, value) {
    if(value == 0)
        return $('<span>', {'class': 'text-muted'}).html(text);

    if(value < 35)
        return $('<span>', {'class': 'text-muted'}).html(text);

    if(value < 45)
        return $('<span>', {'class': ''}).html(text);

    if(value < 50)
        return $('<span>', {'class': 'text-warning'}).html(text);

    return $('<span>', {'class': 'text-danger'}).html(text);
}

//
// compute an uptime (days or hours supported)
//
function uptime(value) {
	var days = value / 86400;

	if(days >= 2)
		return Math.floor(days) + ' days';

	if(parseInt(days) == 1)
		return Math.floor(days) + ' day';

    if(parseInt(value) > 3600)
	    return Math.floor(value / 3600) + ' hours';

	return Math.floor(value / 60) + ' min';
}

function uptime_color(value) {
	if(value < 3600)
		return {'class': 'text-danger'};

	if(value < 86400)
		return {'class': 'text-warning'};

	return {'class': 'text-success'};
}

//
// return a celcius degree if exists
//
function degree(value, limit) {
	if(!value)
		return '<small>-</small>';

	return value + '°C';
}

//
// return formated percent format with different colors
// scaled with value. optional output text can be used
//
function percent(value, extra) {
	return value + ' %' + ((extra) ? ' (' + extra + ')' : '');
}

//
// build a 'summary' table node line
//
function sc(x) { // strip class hotfix
    return x["class"];
}

function summary_node(id, node, server) {
    let header = $("#rtinfo-node-" + id + " .card-header");
    let body = $("#rtinfo-node-" + id + " .card-body");

    var status = {'class': ''};

    if(node.lasttime + 30 < server.servertime)
        status['class'] = 'node-down';

    var tr = $('<tr>', status);

    var status = 'text-success';

    if(node.lasttime + 5 < server.servertime)
        status = 'text-warning';

    if(node.lasttime + 30 < server.servertime)
        status = 'text-danger text-bg-danger';

    header.html(node.hostname);
    header.removeClass("text-bg-danger text-danger text-warning text-success").addClass(status);

    body.empty();

    let cpu = node.cpu_usage[0];
    body.append($("<span>", {"class": "badge rounded-pill bg-dark mx-1 " + sc(colorize(cpu))}).html("CPU " + cpu + " %"));

    let ram = percentvalue(node.memory.ram_used, node.memory.ram_total);
    body.append($("<span>", {"class": "badge rounded-pill bg-dark mx-1 " + sc(colorize(ram))}).html("RAM " + ram + " %"));

    if(node.lasttime + 30 < server.servertime) {
        let up = uptime(elapsed_time(node.lasttime)[0]);
        body.append($('<span>', {"class": "badge rounded-pill bg-dark mx-1"}).html("Down " + up));

    } else {
        let up = uptime(node.uptime);
        body.append($('<span>', {"class": "badge rounded-pill bg-dark mx-1 " + sc(uptime_color(node.uptime))}).html(up));
    }

    /*
    tr.append($('<td>', {'class': status}).append(hostname));

    var swap = 0;
    if(node.memory.swap_total > 0)
        swap = node.memory.swap_total - node.memory.swap_free;

    for(var index in node.loadavg)
        node.loadavg[index] = parseFloat(node.loadavg[index]).toFixed(2);

    var cpunr = node.cpu_usage.length - 1;
    var ram   = percentvalue(node.memory.ram_used, node.memory.ram_total);
    var swap  = node.memory.swap_total - node.memory.swap_free;
    var pswap = percentvalue(swap, node.memory.swap_total);

    tr.append($('<td>', colorize(node.cpu_usage[0]))
        .html($('<span>', {'class': 'wfix'}).html(percent(node.cpu_usage[0]))));

    var size = autosize(node.memory.ram_used);
    tr.append($('<td>', colorize(ram)).html(percent(ram, size)));

    var size = autosize(swap);
    if(node.memory.swap_total > 0)
        tr.append($('<td>', colorizesw(pswap, swap)).html(percent(pswap, size)));

    else tr.append($('<td>').html('-'));

    tr.append($('<td>', loadcolor(node.loadavg[0], cpunr)).html(node.loadavg[0]));
    tr.append($('<td>', loadcolor(node.loadavg[1], cpunr)).html(node.loadavg[1]));
    tr.append($('<td>', loadcolor(node.loadavg[2], cpunr)).html(node.loadavg[2]));
    tr.append($('<td>').html(node.remoteip));
    tr.append($('<td>').html(unixtime(node.time)));

    var up = uptime(node.uptime);
    tr.append($('<td>', uptime_color(node.uptime)).html(up));

    tr.append($('<td>').html(colorcputemp(degree(node.sensors.cpu.average), node.sensors.cpu.average)));

    // disk usage
    var speed = 0
    for(var idx in node.disks)
        speed += node.disks[idx].read_speed + node.disks[idx].write_speed;

    tr.append($('<td>', colordisk(speed)).html(rate(speed)));

    // network usage (rx)
    var speed = 0
    for(var idx in node.network)
        speed += node.network[idx].rx_rate;

    tr.append($('<td>', colorintf(speed, 10)).html(rate(speed)));

    // network usage (tx)
    var speed = 0
    for(var idx in node.network)
        speed += node.network[idx].tx_rate;

    tr.append($('<td>', colorintf(speed, 10)).html(rate(speed)));

    return tr;
    */
}


//
// build summary table
//
function summary(host, server, nodes) {
    for(var id in nodes) {
        if($("#rtinfo-node-" + id).length == 0) {
            let card = $("<div>", {"id": "rtinfo-node-" + id, "class": "card text-bg-dark"});
            let head = $("<div>", {"class": "card-header"}).html("Node " + id);
            let body = $("<div>", {"class": "card-body"});

            card.append(head).append(body);
            $("#rtinfo-content").append(card);
        }

        summary_node(id, nodes[id], server);
    }
}

function arraymove(arr, fi, di) {
    var element = arr[fi];
    arr.splice(fi, 1);
    arr.splice(di, 0, element);
}

//
// parsing new json tree and call required display process
//
function rtinfo_parsing(response, host) {
    // console.log(response);
    var json = response;

	// clearing everyting
	$('body').attr('class', 'connected');

	// ordering hostname
	var hosts = [];
	var nodes = [];

	for(var x in json.rtinfo)
		hosts.push(json.rtinfo[x].hostname);

	hosts = hosts.sort();

	for(var n in hosts)
		for(var x in json.rtinfo)
			if(json.rtinfo[x].hostname == hosts[n])
				nodes.push(json.rtinfo[x]);

	// iterate over differents part showable/hiddable
	summary(host, json, nodes);
}

function camera_update(caminfo) {
    for(var id in caminfo) {
        let camdata = caminfo[id];
        // console.log(camdata);

        let modifier = "timestamp=" + new Date().getTime();
        let location = "http://thumbnail.magibux.maxux.net/small-" + camdata['name'] + ".jpg?" + modifier;

        if($("#camera-" + camdata['id']).length) {
            // refresh tag
            var image = $("#camera-" + camdata['id']);
            image.attr("src", location);

        } else {
            // create new tag
            var target = "#camera-wide";

            if((camdata['image_width'] / camdata['image_height']) < 1.5)
                target = "#camera-regular";

            var image = $('<img>', {'id': 'camera-' + camdata['id'], 'class': 'rounded'});
            image.attr("src", location);

            $(target).append(image);
        }
    }
}

function plurial(amount, word) {
    if(amount.toFixed(0) < 2)
        return word;

    return word + "s";
}

function elapsed_time(source) {
    let now = new Date().getTime() / 1000;
    let uptime = Math.abs(source - now);

    if(uptime < 2)
        return [uptime, "right now"];

    if(uptime < 60)
        return [uptime, uptime.toFixed(0) + plurial(uptime, " second")];

    if(uptime < 3600) {
        let minutes = uptime / 60;
        return [uptime, minutes.toFixed(0) + plurial(minutes, " minute")];
    }

    if(uptime < 86400) {
        let hours = uptime / 3600;
        return [uptime, hours.toFixed(0) + plurial(hours, " hour")];
    }

    let days = uptime / 86400;
    return [uptime, days.toFixed(0) + plurial(days, " day")];
}

let temperature_sensors = {
    "28-ff641e93a11cb3": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641e93b9a587": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641e93b543fe": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641e93b5b7eb": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641f7593ab27": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641f43f47d96": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
    "28-ff641f43ca63e5": [[5, "secondary"], [20, "info"], [27, "success"], [38, "danger"], [60, "dark"]],
};

function temperature_update(sensors) {
    for(var id in sensors) {
        let sensor = sensors[id];
        let value = sensor["value"].toFixed(2) + "°C";
        let uptime = elapsed_time(sensor["changed"]);

        if($("#temperature-" + id).length == 0) {
            var root = $("<div>", {"id": "temperature-" + id, "class": "row"});

            var namediv = $("<div>", {"class": "col-6"});
            namediv.append($("<div>", {"class": "name font-monospace"}).html(id));

            var valdiv = $("<div>", {"class": "col-2"});
            valdiv.append($("<span>", {"class": "value badge rounded-pill bg-info text-dark"}).html(value));

            var updiv = $("<div>", {"class": "col-4 text-end font-monospace"});
            updiv.append($("<span>", {"class": "uptime badge rounded-pill bg-dark"}).html(uptime[1]));

            root.append(namediv).append(valdiv).append(updiv);
            $("#temperature").append(root);
        }

        // update value with correct colorartion
        $("#temperature-" + id + " .value").removeClass().addClass("value badge rounded-pill");

        // update badge color
        if(temperature_sensors[id] !== undefined) {
            for(let idx in temperature_sensors[id]) {
                let threshold = temperature_sensors[id][idx];

                if(sensor["value"] < threshold[0]) {
                    $("#temperature-" + id + " .value").addClass("text-bg-" + threshold[1]);
                    break;
                }
            }
        }

        $("#temperature-" + id + " .value").html(value);
        $("#temperature-" + id + " .uptime").html(uptime[1]);
    }
}

function get_current_time() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const secondes = String(now.getSeconds()).padStart(2, '0');
    const current_time = `${hours}:${minutes}:${secondes}`;
    return current_time;
}
function tanks_update(id, sensor) {
    let unit = [0, 2, 3, 4, 9];
    let brakes = [5, 7, 8];
    for (var i in unit) {
        if (unit[i] == id) {
            if (sensor['value'] < 3)
                return ("bg-danger text-light");
            else if (sensor['value'] < 6)
                return ("bg-warning text-dark");
            else
                return ("bg-success text-light");
        }
    }
    for (var f in unit) {
        if (brakes[f] == id)
            return (sensor['value'] > 1.2 ? "bg-info text-dark" : "bg-secondary text-dark");
    }
    return (sensor['value'] > 1.4 ? "bg-success text-light" : "bg-secondary text-dark");
}

function pressure_update(sensors) {
    for(var id in sensors) {
        let sensor = sensors[id];
        let value = sensor['value'].toFixed(2) + " bar";
        let uptime = elapsed_time(sensor["time"]);

        if($("#pressure-" + id).length == 0) {
            var root = $("<div>", {"id": "pressure-" + id, "class": "row"});

            var namediv = $("<div>", {"class": "col-5"});
            namediv.append($("<div>", {"class": "name"}).html("Channel " + (parseInt(id) + 1)));

            var valdiv = $("<div>", {"class": "col-3"});
            valdiv.append($("<span>", {"class": "value badge rounded-pill bg-info text-dark"}).html(value));

            var updiv = $("<div>", {"class": "col-4 text-end font-monospace"});
            updiv.append($("<span>", {"class": "uptime badge rounded-pill bg-dark"}).html(uptime[1]));

            root.append(namediv).append(valdiv).append(updiv);
            $("#pressure").append(root);
        }
        // update value with correct colorartion
        let color = tanks_update(id, sensor);
        $("#pressure-" + id + " .value").removeClass("bg-success bg-dark bg-info bg-secondary text-dark text-light bg-warning bg-danger").addClass(color).html(value);
        $("#pressure-" + id + " .uptime").html(uptime[1]);
    }
}

function location_update(location) {
    let lat = location['coord']['lat'].toFixed(6);
    let lng = location['coord']['lng'].toFixed(6);
    let place = location['place'];

    $("#coord").html(lat + ", " + lng);
    $("#locality").html(place[0] + ", " + place[1]);
    $("#speed").html(location['speed'].toFixed(0));

    $("#trip").html((location['trip'] / 1000).toFixed(2));
    $("#odometer").html((location['odometer'] / 1000).toFixed(2));
}

function relays_update(state) {
    let names = [
        "Light - Main Service",
        "Light - Front Pannel",
        "Light - LED Bar (left)",
        "Light - LED Bar (right)",
        "Drink - Main Fridge",
        "Cameras - Primary",
        "Cameras - Secondary",
        "Light - Infrared",
    ];

    for(var channel in state) {
        let value = state[channel][0] ? "Online" : "Offline";
        let name = names[channel];
        let uptime = elapsed_time(state[channel][1]);

        if($("#relay-channel-" + channel).length == 0) {
            var root = $("<div>", {"id": "relay-channel-" + channel, "class": "row"});
            var nametag = $("<div>", {"class": "col-6 name"}).html(name);

            var sensortag = $("<div>", {"class": "col-2"});
            sensortag.append($("<span>", {"class": "value badge rounded-pill"}).html(value));

            var uptimetag = $("<div>", {"class": "col-4 text-end font-monospace"});
            uptimetag.append($("<span>", {"class": "uptime badge rounded-pill bg-dark"}).html(uptime[1]));

            root.append(nametag).append(sensortag).append(uptimetag);
            $("#relays").append(root);
        }

        // only update value
        let color = (state[channel][0] ? "bg-success" : "bg-dark");
        $("#relay-channel-" + channel + " .value").removeClass("bg-success bg-dark").addClass(color).html(value);
        $("#relay-channel-" + channel + " .uptime").html(uptime[1]);
    }
}

var socket;
var caminfo;
var backlog = {
    "relay": [],
    "temperature": [],
    "pressure": [],
};

function update_hours_time() {
    $("#current-time").html(get_current_time());
}

function recurring() {
    update_hours_time();
    update_relays_time();
    update_temperature_time();
    update_pressure_time();
}

function update_relays_time() {
    for(var channel in backlog['relay']) {
        let relay = backlog['relay'][channel];

        let uptime = elapsed_time(relay[1]);
        $("#relay-channel-" + channel + " .uptime").html(uptime[1]);
    }
}

function update_temperature_time() {
    for(var id in backlog['temperature']) {
        var sensor = backlog['temperature'][id];

        let uptime = elapsed_time(sensor["changed"]);
        var tag = $("#temperature-" + id + " .uptime");

        tag.html(uptime[1]);
        tag.removeClass("text-danger");

        if(uptime[0] > 60)
            tag.addClass("text-danger");
    }
}

function update_pressure_time() {
    for(var id in backlog['pressure']) {
        let sensor = backlog['pressure'][id];

        let uptime = elapsed_time(sensor['time']);
        $("#pressure-" + id + " .uptime").html(uptime[1]);
    }
}

function relay_ajax(source) {
    source.preventDefault();
    let target = $(source.target).attr("href");

    $.get(target);
}

function connect() {
    socket = new WebSocket("ws://monitoring.magibux.maxux.net:30900/");

    socket.onopen = function() {
        console.log("websocket open");
        $('#disconnected').hide();
    }

    socket.onmessage = function(msg) {
        json = JSON.parse(msg.data);

        backlog[json['type']] = json['payload'];
        // console.log(json);

        switch(json['type']) {
            case "cameras":
                return camera_update(json['payload']);
            break;

            case "rtinfo":
                return rtinfo_parsing(json['payload'], 'magibux');
            break;

            case "location":
                return location_update(json['payload']);
            break;

            case "temperature":
                return temperature_update(json['payload']);
            break;

            case "pressure":
                return pressure_update(json['payload']);
            break;


            case "relay":
                return relays_update(json['payload']);
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

function fresh_reload() {
    window.location.reload();
}

$(document).ready(function() {
    setInterval(recurring, 1000);
    setTimeout(fresh_reload, 3600000);

    // set relays button ajax
    $(".relay-button").each(function(index) {
        $(this).on("click", relay_ajax);
    });

    connect();
});

