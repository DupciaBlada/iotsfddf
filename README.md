Aplikacja Rozpoznawania Mowy, Obiektów w Wideo oraz Pomiaru Temperatury z Wizualizacją w Grafanie
Opis Projektu

Projekt ten łączy technologie IoT, uczenie maszynowe i wizualizację danych, tworząc inteligentny system. Główne funkcjonalności obejmują:
Pomiar Temperatury

    Mikrokontroler ESP8266 mierzy temperaturę otoczenia za pomocą czujnika DS18B20.
    Wynik pomiaru jest wyświetlany w terminalu środowiska Arduino IDE oraz wysyłany do zdalnego brokera MQTT z użyciem szyfrowania i uwierzytelniania użytkownika.

Konwersja Mowy na Tekst

    Program w Pythonie wykorzystuje model Whisper do zamiany mowy w języku polskim na tekst.
    Przetworzony tekst jest przesyłany do brokera MQTT w celu dalszego wykorzystania.

Konwersja Wideo na Tekst

    Drugi program w Pythonie używa modelu YOLO do wykrywania obiektów w klatkach wideo, nazywania ich oraz wysyłania opisów do brokera MQTT.

Wyświetlanie Tekstu na Ekranie LCD

    ESP8266 odbiera tekst (z modułów Mowa-na-Tekst i Wideo-na-Tekst) z brokera MQTT.
    Tekst jest wyświetlany na podłączonym ekranie LCD:
        Górna linia: tekst z modułu rozpoznawania mowy.
        Dolna linia: tekst z modułu rozpoznawania obiektów w wideo.

Gromadzenie i Wizualizacja Danych

    Dane o temperaturze są zapisywane w bazie danych InfluxDB za pomocą aplikacji w Pythonie działającej jako subskrybent MQTT.
    Grafana umożliwia wizualizację danych temperaturowych w czasie rzeczywistym na konfigurowalnych pulpitach.

    Instrukcja Instalacji

Wykonaj poniższe kroki, aby skonfigurować i uruchomić projekt. Przewodnik zakłada podstawową znajomość Dockera, Pythona oraz ESP8266.
Wymagania Wstępne
Oprogramowanie:

    Arduino IDE
    Python (wersja 3.8 lub nowsza)
    Docker i Docker Compose
    Git

Sprzęt:

    Mikrokontroler ESP8266
    Czujnik temperatury DS18B20
    Wyświetlacz LCD

Konta:

    Konto w Grafanie oraz na brokerze MQTT (jeśli używany jest system oparty na chmurze)

    Krok 1: Sklonuj Repozytorium

Otwórz terminal i sklonuj repozytorium projektu:

git clone https://github.com/your-repo-name/project.git  
cd project  
Krok 2: Konfiguracja Kontenerów Dockera

Utwórz plik docker-compose.yml, aby uruchomić następujące usługi:

    InfluxDB: Baza danych do przechowywania danych o temperaturze.
    Grafana: Panel do wizualizacji danych.
    Subscriber: Skrypt Python subskrybujący MQTT i zapisujący dane.

Przykładowy plik docker-compose.yml:
version: '3.8'

networks:
  monitoring_network:
    driver: bridge

services:
  influxdb:
    image: influxdb:latest
    container_name: influxdb
    ports:
      - "8086:8086"
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword
      - DOCKER_INFLUXDB_INIT_ORG=my-org
      - DOCKER_INFLUXDB_INIT_BUCKET=temp-data
      - DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=MON-CZ1fE090xmJQ-e0sdZNgjL8mz3sNTpgRsHlsV14rNVc1kNufRcHuN33c3xl1rrneA1PliyNRrvr88q51Rg==
    volumes:
      - influxdb_data:/var/lib/influxdb
    networks:
      - monitoring_network

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=adminpassword
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - influxdb
    networks:
      - monitoring_network

  subscriber:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: subscriber
    depends_on:
      - influxdb
    environment:
      - MQTT_BROKER=h7349222.ala.eu-central-1.emqxsl.com
      - MQTT_PORT=8883
      - MQTT_USERNAME=chatadoriana
      - MQTT_PASSWORD=chatadoriana
      - MQTT_TOPIC=emqx/esp8266
      - INFLUXDB_URL=http://influxdb:8086/
      - INFLUXDB_TOKEN=MON-CZ1fE090xmJQ-e0sdZNgjL8mz3sNTpgRsHlsV14rNVc1kNufRcHuN33c3xl1rrneA1PliyNRrvr88q51Rg==
      - INFLUXDB_ORG=my-org
      - INFLUXDB_BUCKET=temp-data
    networks:
      - monitoring_network

volumes:
  influxdb_data:
  grafana_data:
  Krok 3: Wgraj Oprogramowanie na ESP8266

    Otwórz plik esp8266.ino w Arduino IDE.
    Zainstaluj wymagane biblioteki:
        OneWire
        DallasTemperature
        PubSubClient
    Zaktualizuj ustawienia w kodzie:
        Dane logowania do brokera MQTT (adres, port, nazwa użytkownika i hasło).
        Dane WiFi (SSID i hasło).
    Wgraj kod na mikrokontroler ESP8266 za pomocą Arduino IDE.

Upewnij się, że ESP8266 jest poprawnie podłączony do komputera i wybrany jest odpowiedni port COM oraz model płyty.
Krok 4: Zainstaluj Wymagane Biblioteki Python

    Utwórz środowisko wirtualne:

python3 -m venv venv  
source venv/bin/activate  

Zainstaluj wymagane pakiety:

    pip install -r requirements.txt  

Upewnij się, że wszystkie zależności zostały poprawnie zainstalowane, aby uniknąć problemów podczas działania aplikacji.

Krok 5: Uruchom Programy Rozpoznawania Mowy i Analizy Wideo

    Rozpoznawanie mowy (Speech-to-Text):
    Przejdź do folderu z programem:

cd speech-to-text  
python speech_to_text.py  

Analiza wideo (Video-to-Text):
Przejdź do odpowiedniego folderu:

    cd video-to-text  
    python video_to_text.py  

Każdy z programów powinien rozpocząć działanie, wysyłając dane tekstowe do brokera MQTT. Upewnij się, że oba programy są poprawnie skonfigurowane i mają dostęp do niezbędnych zależności.

Krok 6: Skonfiguruj Grafanę

    Otwórz Grafanę w przeglądarce pod adresem:

    http://localhost:3000  

    Dodaj InfluxDB jako źródło danych:
        Przejdź do ustawień źródeł danych w Grafanie.
        Wypełnij pola:
            URL: http://influxdb:8086
            Baza danych: temperature
            Uwierzytelnianie: Wprowadź dane logowania zdefiniowane w pliku docker-compose.yml (np. użytkownik: admin, hasło: admin_password).

    Utwórz dashboard:
        Dodaj nowy panel.
        Skonfiguruj zapytanie do InfluxDB, aby wyświetlić dane o temperaturze w czasie rzeczywistym.
        Dostosuj wykresy i widoki według potrzeb.

Po skonfigurowaniu Grafana będzie wizualizować dane przesyłane z czujnika temperatury.
Użycie

    Uruchom ESP8266 i połącz go z WiFi:
        Upewnij się, że urządzenie jest zasilane i skonfigurowane do połączenia z siecią WiFi.

    Mowa na Tekst (Speech-to-Text):
        Mów do mikrofonu. System przetworzy mowę i prześle wyniki do brokera MQTT.

    Wideo na Tekst (Video-to-Text):
        Włącz źródło wideo. System wykryje obiekty, nazwie je i prześle opisy do brokera MQTT.

    Wyświetlanie wyników:
        Ekran LCD:
            Górna linia: Wyniki z modułu Mowa na Tekst.
            Dolna linia: Wyniki z modułu Wideo na Tekst.
        Grafana:
            Otwórz dashboard, aby obserwować dane o temperaturze w czasie rzeczywistym.

Autorzy: 
Wiktor Garbowicz
Kamil Golec
Bartosz Lamprycht
