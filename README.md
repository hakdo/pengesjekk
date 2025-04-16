# Pengesjekk

Dette er en enkel regnskapsapp laget med Python/tkinter. Koden er 99% generert av Mistral AI via chatbot'en Le Chat. 

App-en kjører lokalt, og har støtte for automatisk import av transaksjoner i Excel-format fra eksport fra nettbanken til Eika-bankene, og CSV-import fra Sparebank1.

App-en har en automatisk funksjon for kategorisering av transaksjoner med en KI-agent som kjører i Mistrals "La Platforme". Denne krever en API-nøkkel. Om du ønsker å bruke denne funksjonen får du lage din egen agent :). Den eneste filen som har noen avhengighet her er `categorizer.py`.

## Sikkerhet
Transaksjonene lagres i en lokal sqlite-database. Det er ingen passord eller andre beskyttelsesmekanismer utover filsystemet. Sett rettigheter, tilgang og logging ved hjelp av operativsystemet her. 

Den eneste nettbaserte tjenesten er automatisk kategorisering ved hjelp av en agent som kjører på Mistrals La Platforme. Tilgangen her er gitt via en API-nøkkel, som app'en henter fra en miljøvariabel. 