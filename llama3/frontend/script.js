// Weather forecast API script
const weatherApiKey = '0fd743b3945f49359c0223712242307';
const query = 'Sarajevo';

fetch(`http://api.weatherapi.com/v1/current.json?key=${weatherApiKey}&q=${query}`)
    .then(response => response.json())
    .then(data => {
        const weatherDiv = document.getElementById('weather');
        const location = data.location.name;
        const country = data.location.country;
        const tempC = data.current.temp_c;
        const condition = data.current.condition.text;
        const windKph = data.current.wind_kph;
        const humidity = data.current.humidity;
        let recommendation = "The perfect weather for sightseeing!";

        if (tempC > 25) {
            recommendation = "It's a hot day! Dress lightly.";
        } else if (tempC < 15) {
            recommendation = "It's a cold day! Put on some layers.";
        } else {
            recommendation = "The perfect temperature for sightseeing. Put it to good use!";
        }

        if (windKph > 20) {
            recommendation += " It's quite windy today! Hold onto your hat.";
        } else if (windKph < 5) {
            recommendation += " Calm winds today. Great weather for a stroll.";
        } else {
            recommendation += " Mild breeze today. Enjoy your day!";
        }

        weatherDiv.innerHTML = `
            <p><strong>Location:</strong> ${location}, ${country}</p>
            <p><strong>Temperature:</strong> ${tempC}°C</p>
            <p><strong>Condition:</strong> ${condition}</p>
            <p><strong>Wind:</strong> ${windKph} kph</p>
            <p><strong>Humidity:</strong> ${humidity}%</p>
            <p><strong>Recommendation: </strong> ${recommendation} </p>
        `;
    })
    .catch(error => console.error('Error fetching weather data:', error));

// Google Maps JavaScript API
let map;
let previousCoordinates = {};

//initializes the google map and sets up continuos polling, looking for new coordinates at set intervals
function initMap() {
    const sarajevo = { lat: 43.85, lng: 18.38 };
    map = new google.maps.Map(document.getElementById("map"), {
        zoom: 12,
        center: sarajevo,
        mapTypeId: "roadmap"
    });

    setInterval(fetchCoordinates, 5000); 
}
//fetches coordinates from the server and updates the map if there are any new coordinates
function fetchCoordinates() {
    fetch('http://localhost:5000/get_coordinates')
        .then(response => response.json())
        .then(data => {
            if (JSON.stringify(data) !== JSON.stringify(previousCoordinates)) {
                previousCoordinates = data;
                updateMap(data);
            }
        })
        .catch(error => console.error('Error fetching coordinates:', error));
}
//updates the map by placing new markers with the given coordinates
function updateMap(coordinates) {
    if (!map.markers) {
        map.markers = [];
    }

    map.markers.forEach(marker => marker.setMap(null));
    map.markers = [];

    for (const [name, coords] of Object.entries(coordinates)) {
        const marker = new google.maps.Marker({
            position: { lat: coords[0], lng: coords[1] },
            map: map,
            title: name
        });
        map.markers.push(marker);
    }
}

window.addEventListener('load', initMap);