2. **Umbenennen [rename]**\: Die Dateien werden entsprechend des Erstelldatums umbenannt, so dass sie „YYYY-MM-DD_HH.MM.SS\_#.“ heißen, mit #=alter Name und sie ihre alte Endung behalten, wobei jedoch die Endung je Medientyp immer nur eine Variante haben soll (jpeg->jpg, MP4->mp4, etc). 

   In XMP zu hinterlegen (siehe [Dublin-Core (dc) XMP Namespace](https://de.wikipedia.org/wiki/Dublin_Core)):
   * die Ursprüngliche Aufnahmezeit soll in *dc:date* abgelegt werden
   * der ursprüngliche Dateiname soll unter *dc:source* abelegt werden