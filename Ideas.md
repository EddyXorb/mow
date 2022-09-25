# Photoworkflow

## Überblick

Es gibt 4 verschiedene Medientypen (jpg, raw, audio und video) die

* gesichtet/aussortiert
* bearbeitet
* umbenannt
* gesichert

gehören.

Es gibt weiters drei relevante Dateispeicherorte in diesem Prozess

* der **Quell**\-Speicherort mit den Originaldateien (meist SD-Karte)
* ein **intermediärer** Speicherort, wo etwaige Bearbeitungsschritte mit Kopien der Quellmedien stattfinden
* ein **finaler** Sicherungsort (oder mehrere)

Der finale Sicherungsort ist bisher und soll es weiterhin sein ein Ordner wie z.B. „2022-11-12 Geburtstag“ in dem sich alle zu diesem Ereignis gehörenden Bilder befinden. Dieser Ordner wird im weiteren **Ereignisorder** genannt.

## Bisherige Arbeitsweise

 1. Alle ungesicherten Medien werden von der SD-Karte in einem lokalen Verzeichnis `_noch_einsortieren` auf meinen PC kopiert

 2. in diesem Verzeichnis findet das automatische Clustering + die Umbennnung der Dateien statt. Dabei werden alle jpg-raw-file-Paare in unterordner verschoben, die von der Aufnahmezeit der Fotos abhängen. Die Umbennung erfolgt auch dabei, so dass jedes Foto/video den Zeitpunkt der Aufnahme im Namen trägt.
   
 3. Danach beginnt die eigentliche Arbeit. Üblicherweise ist das Clustering zu filigran und einige Ordner können wieder zusammengefasst werden, händisch.

 4. Den geclusterten Fotos/videos wird je ein cluster-namen gegeben, z.B. "Wochenendausflug". Dies passiert implizit über den sie enthaltenden Ordnernamen.

 5. Nun wird chronologisch jeder Ordner durchgegangen und die unschönen Fotos werden gelöscht, samt den Rohdateien. Fotos die zwar ok, aber nicht herausragend sind, behalte ich, aber nur als jpg, die Rohdatei kommt weg. Dies alles meist mit XNView MP händisch, sowohl sichten als auch löschen.

 6. Als optionaler Zwischenschritt erfolgt die Bearbeitung einer besonderer Fotos mit Lightroom. Dies wird aus XNView MP heraus aufgerufen.

 7. Als weiterer optionaler Zwischenschritt werden Videos mit Handbrake konvertiert und auch umbenannt. Das Zuordnen der Videos zu den Ordnern erfolgt händisch. Bisher sind sie immer im Unterordner `videos` zu finden.

 8. Zum Abschluss wird der fertige Ordner aus `_noch_einsortieren` in den jeweiligen Jahresordner, der sich lokal auf meinem Rechner befindet und von Nextcloud synchronisiert wird.

 9.  Was ich oft vergesse: das Backup auf der NAS mit dem neuen Ordner zu füttern, das nicht an die Nextcloud angeschlossen ist.

1.  Fotos an Personen senden, die bei den betreffenden Ereignissen dabei waren bzw. ein Interesse daran haben

2.  Wenige Male im Jahr: Fotos ausdrucken entweder als Fotobuch oder einzelne Fotos die verschickt/ verschenkt werden

## Probleme mit der bisherigen Arbeitsweise

 1. [*pausen*] oft wird die Arbeit **unterbrochen**, so dass ich beim nächsten Mal nicht immer sicher weiß, wo ich war. Dies betrifft auch insbesondere die fotos auf der SD-Karte, wo ich oft genau schauen muss, ob sie schon rüberkopiert wurden oder nicht. Aber auch das aussortieren, clustern und nachbearbeiten vergesse ich manchmal oder mache es doppelt. Ich habe auch keine ganz feste **Reihenfolge** was ich als nächstes mache in dem workflow; manchmal vertausche ich die Reihenfolge, was immer mühsam ist sich zu erinnern was noch aussteht.

 2. [*speicher*] Bisher kopiere ich alle Dateien vom *Quell*\-Medium in das *intermediäre* Verzeichnis. Dort liegen sie manchmal recht lange und nehmen vor allem sehr viel **Speicherplatz** weg, obwohl ich die meisten Fotos darin eh nicht in Raw behalten möchte, was ich aber erst nach dem Aussortierschritt wirklich reduziere.

 3. [*videos*] Die **Videos** benötigen eine Sonderbehandlung, und sie nehmen ebenso sehr viel Speicherplatz ein, solange diese nicht abgeschlossen ist. Das Einsortieren der Videos in die jeweiligen Ordner ist nervig und zeitraubend. Die Videos werden manchmal nicht umbenannt, weil es einfach vergessen wird und dann steckt im Videonamen nicht mehr die Information über den Entstehungszeitpunkt des Videos, da nach der Konvertierung die Metadaten (Erstellzeitpunkt) verändert wurden. Die Tatsache, dass die Videos in einem Unterordner *videos* liegen stört auch, da sie sich so nicht chronologisch in die Fotos einreihen.

 4. [*kategorien*] Es gibt manchmal herausragende Fotos, die ich doppelt sichere in einem Ordner `_schönste`, oder Fotos die einer bestimmten **Kategorie** zuzuordnen sind, wie z.B. `_greifen` oder `_Kirchen`, die auch doppelt gespeichert werden und meist eine Sonderbehandlung benötigen. Dies kostet Speicherplatz und Zusatzaufwand.

 5. [*lightroom*] Es kommt oft dazu, dass ich noch im intermediären Ordner Fotos mit **Lightroom** bearbeite. Wenn ich sie dann verschiebe in den finalen Ordner, weiß Lightroom nicht mehr, wo die bereits bearbeiteten Fotos hin sind. Man kann die Zuordnung dann händisch reparieren, was aber Zeit kostet und nervig ist.

 6. [*backups*] Oft vergesse ich die Fotos in der NAS zu **sichern** in dem Ordner, der nicht über die Nextcloud synchronisiert wird.

 7. [*bewertung*] Zwar habe ich beim durchschauen einen **Überblick** gewonnen, welche Bilder ganz besonders gut sind, dieser Überblick geht aber mit der Zeit **verloren** und im Nachhinein muss ich wieder alle durchschauen um die **schönste**n Bilder eines Ereignisses zu finden.

 8. [*personen*] Um Ereignisse mit bestimmten Personen zu finden, suche ich nach den PersonenNamen in den Ereignisordnernamen, was nicht immer zuverlässig ist und auch nicht an die Fotos darin gebunden ist.

 9.  [*weiterleitung*] manchmal vergesse ich Personen die Fotos zukommen zu lassen

10.  [*ausdrucken*] es ist sehr mühevoll geeignete Fotos für die Fotobücher zusammenzustellen. Die Fotos werden bisher immer von neuem gesichtet und die geeignetsten in einen extra Ordner kopiert, wo sie dann weiterverarbeitet werden als Fotobuch oder Direktausdruck. Der Ordner mit den zu druckenden Fotos bleibt dabei meist bestehen, was zu doppelt gespeicherten Fotos führt.


11.  [*gps]* bis jetzt gibt es keine Möglichkeit für mich eventuelle Ortsangaben in die Exifs der Bilder hinzuzufügen.

## Wünsche an den neuen Workflow

 1. [*Unterbrechbarkeit*] Immer wissen, wo man das letzte Mal aufgehört hat.
   
 2. [*Redundanzvermeidung*] Nichts doppelt machen müssen, nichts doppelt speichern.
   
 3. [*Sicherheit*] Es darf nichts durch kleinere Unaufmerksamkeiten verloren gehen, insbesondere keine Mediendateien.
   
 4. [*Übersichtlichkeit*] Es soll nichts dergestalt automatisiert werden, dass nicht auch ohne ein bestimmtes Programm der Überblick behalten wird, wo im Workflow man sich gerade befindet.
   
 5. [*Interoperabilität*] Auch wenn Programme zur Vereinfachung des Workflows eingesetzt werden, soll es jederzeit möglich sein auf manuelles Abarbeiten umzusteigen und umgekehrt von manuellem auf automatisches. Dies heißt nicht, dass man dann gewisse Vorteile, die automatikgestütztes Arbeiten mit sich bringt, nicht unter Umständen einbüßt.
   
 6. [*Autarkie und Flexibilität*] Es soll nicht nötig sein, ganz bestimmte Programme zu verwenden um den Workflow zu realisieren, stattdessen soll es möglich sein seine bevorzugten Programme einzusetzen und diese auch zu wechseln.
   
 7. [*Lokalität*] Metainformationen sollen sich möglichst dort befinden worauf sie sich beziehen (und nirgendwo anders).

 8.  [*Nichtserialität*] Es soll möglich sein, eine beliebige Untermenge der zu bearbeitenden Dateien in kürzester Zeit durch alle Stufen des Prozesses zu führen und die Bearbeitung von ihnen damit vorzeitig abzuschließen, ohne dass dadurch etwas durcheinander kommt.
   
 9.  [*Umkehrbarkeit*] Auch wenn man im Workflow bereits weiter vorangeschritten ist soll es ohne viel Aufwand möglich sein für jeden Medientypus Schritte aus den vorherigen Stufen auszuführen, ohne dass es zur Verwirrung kommt.

 1.  [*Platformunabhängigkeit*] Die wesentlichen Schritte des Workflows sollen auf allen meinen Geräten durchgeführt werden können (Windows, Android, IOS), auch wenn dies bedeutet etwas mehr händisch arbeiten zu müssen.

 2.  [*Optionalität*] Es soll bis auf wenige Kernschritte vieles optional bleiben, ohne dass der Workflow dadurch durcheinander gerät.

## Skizze eines neuen Workflows
Die mit einem **\*** gekennzeichnet Schritte sind optional.

1. **Kopieren**: Mediendateien werden von Quell (QV)- ins Intermediärverzeichnis (IV) kopiert, im Quellverzeichnis wird eine Datei [source.cr](http://source.cr) angelegt mit einer noch zu definierenden Struktur aus der hervorgeht welche Dateien bereits kopiert wurden. 
   
   *Idee:* Es wäre Wünschenswert, wenn man am Ende des Prozesses einen Abgleich machen kann, ob alle Dateien die als bereits kopiert gekennzeichnet wurden, auch verarbeitet wurden. Das Problem dabei sind die im Aussortiersschritt gelöschten Fotos, die natürlich nicht als fehlend markiert werden sollen bei diesem Abgleich. Eine Möglichkeit wäre es, die zum Löschen ausgewählten Fotos in einer Liste "deleted.yml" abzulegen, dies ist händisch aber nur schlecht möglich und würde das Ziel, interoperabel zu sein, gefährden.

1. **Umbenennen\***: Im IV mit noch zu definierendem Ort und Namen werden die Dateien entsprechend des Erstelldatums umbenannt, so dass sie „YYYY-MM-DD_HH.MM.SS\_#.“ heißen, mit #=alter Name und sie ihre alte Endung behalten, wobei jedoch die Endung je Medientyp immer nur eine Variante haben soll (jpeg->jpg, MP4->mp4, etc). Falls die Änderung des Dateinamens erfolgt, soll in einem passenden XMP-Tag der originale Name hinterlegt werden:
      * die Ursprüngliche Aufnahmezeit soll in *dc:date* abgelegt werden
      * der ursprüngliche Dateiname soll unter *dc:source* abelegt werden

2. **Konvertieren\***: Ausgewählte Medien (insbesondere Videos) werden in diesem Schritt kleinergerechnet. Die originalen Medien (nur IV) werden sofort gelöscht. Konvertierte Dateien bekommen das Suffix „\_converted“ im Dateinamen, um sofort zu sehen welche Medien noch nicht konvertiert wurden.

3. **Gruppieren**: Medien desselben Ereignisses werden zusammengefasst, indem für jedes Ereignis ein Unterordner angelegt wird, der YYYY-MM-DD_HH #“ heißt, mit der Zeit entsprechend dem Aufnahmezeitpunkt des ersten Mediums und #=Name des Ereignisses. Optional werden nur die Videos und die *.jpgs* in die Ereignisordner gepackt, die Raws verbleiben vorerst im Wurzelverzeichnis des IV. Dies erleichtert das Scrollen und nachfolgende Bewerten.

   Nach Fertigstellung wird eine leere versteckte Datei `.clustered` angelegt, die anzeigt, dass man fertig ist mit dem Gruppieren.

   Es sollen alle Medien dieses Ereignisses einen XMP-Tag befüllen, dessen Inhalt dem Namen des Ereignisses entspricht. Dies wird in dem [Dublin-Core (dc) XMP Namespace](https://de.wikipedia.org/wiki/Dublin_Core) abgelegt unter `description`.

4. **XMP-Metadaten befüllen:**

   *Begründung:* Exif als Metadatenspeicher kommt nicht in Frage, weil damit nicht alle Formate abgehandelt werden können wie z.B. `.ORF` und `.mp4`.
   1. **Bewerten/Löschen**: der XMP-Eintrag „Rating“ jedes Mediums wird angelegt und mit Werten von 0 bis 5 versehen. Dabei heißt
      * 0 = unklar, aber behalte raw und jpg
      * 1 = schlecht, behalte nur jpg
      * 2 = ok, behalte nur jpg
      * 3 = gut, behalte nur jpg
      * 4 = sehr gut, behalte jpg und raw
      * 5 = hervorragend, behalte jpg und raw

      Dabei kann das Programm XNView MP eingesetzt werden, oder jedes beliebige, das XMP-Tagging beherrscht. Wichtig dabei: auch die Videos gehören so bewertet.

      ***Fotos/Videos die überhaupt nicht gefallen werden gelöscht, samt RAW.***

      Sollte man den Prozess mittendrin unterbrechen müssen, ist dies dadurch klar, dass nicht alle Medien ein Rating haben.

      Nach Abschluss dieser Stufe wird durch eine leere versteckte Datei namens `.rated` markiert, dass die Bewertung abgeschlossen ist, was Zeit spart und auf den ersten Blick erlaubt händisch zu sehen, dass dies der Fall ist. Versteckt deshalb, weil es meist nicht erforderlich ist sie zu sehen, und weil es so in der Dateisystemauflistung ganz oben steht.
      
   2. **Kategorisieren\***: den Medien können beliebige Kategorien wie „greifen“, „drucken“, „Kirchen“ etc. zugeordnet werden entsprechend meiner fotografischen Projekte. Diese Kategorien werden in einen noch zu definierenden geeigneten XMP-Tag untergebracht. Weiters können hier die mit dem Ereignis verbundenen Personennamen hier aufgenommen werden. Es können in diesem Schritt auch Tools wie [Excire](https://excire.com) Schlagworte erstellen, die in XMP eingebettet werden.
      
   3. **Lokalisieren\***: Medien bekommen einen Ort in die Metadaten geschrieben. Hier wird zwischen einem Ort für alle Medien desselben Ereignisses unterschieden und je einem genauen Ort für jedes Foto. Dies hängt davon ab, ob es einen GPS-Track gibt, der auf die Medien angewendet werden kann und wenn nein, ob es eine einfache Möglichkeit gibt auf einer Karte für ein Ereignis einen ungefähren Ort zu markieren.

 2. **Aggregieren**: die RAWs werden entsprechend dem obigen Ratingschema in den Ereignisordner kopiert bzw. gelöscht. Zugleich werden die in den beiden vorhergehenden Schritten erzeugten XMP-Tags in die RAW-Dateien kopiert. Der Abschluss davon wird ebenso in [progress.cr](http://progress.cr) festgehalten.

 3. **Ablegen**: Ereignisse die bis zu dieser Stufe behandelt wurden, können als grundsätzlich fertig abgearbeitet betrachtet werden und deren Ordner werden in den finalen Ablageort verschoben, was ebenso in [progress.cr](http://progress.cr) markiert wird, bevor es zum Ablegen kommt.

5.  **Sichern**: Hierbei soll zwischen einem einzigen Haupt- und potenziell mehreren Nebensicherungsorten unterschieden werden. Der finale Ablageort ist automatisch der Hauptsicherungsort. Änderungen am finalen Ablageort (Z.B. durch die nächste Stufe) sollen einseitig an die Sicherungsorte durchgereicht werden (so dass die Sicherungsorte möglichst stets gespiegelt zu dem Ablageort sind). Dies wäre keine gute Sicherungsstrategie, wenn die Sicherungen nicht Versionierungen beherrschen würden. Es muss also sichergestellt sein, dass mit dem einseitigen Synchronisieren der Sicherungsorte zumindest eine Zeitlang noch alle Medien wiederhergestellt werden können. Dies sicherzustellen ist nicht Aufgabe dieses Workflows.

6. **Nachbearbeiten\***: jedes Foto mit RAW-Dateien kann nun mit dem Programm der Wahl entwickelt werden. Ein dergestalt nachbearbeitetes Foto sollte sowohl im RAW als auch im jpg hinterlegt bekommen, dass dies geschehen ist, damit beim Wiederaufnehmen der Tätigkeit klar ist, was noch ansteht. Zusätzlich kann in [progress.cr](http://progress.cr) noch stehen welche Fotos noch bearbeitet gehören.

Die Reihenfolge muss nicht fest sein, aber folgendes muss gelten. Dabei bezeichne W die Menge aller Schritte, wie sie oben definiert wurden, und O die Teilmenge davon, die als optional (**\***) markiert ist.

* 1 < w für alle w aus W\\{1}
* 4 < 5 < 8 < 9 < 10
* 2,3 < 5 um zu verhindern, dass beim Konvertieren/Umbenennen XMP-Tags gelöscht/nicht mehr zuordnenbar sind
* 6,7 < 8, damit die gesetzten Tags auch in die RAWs komme