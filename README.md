# vsTAAmbk 0.2
A ported AA-script from Avisynth

For more detial NMM-HD：https://www.nmm-hd.org/newbbs/viewtopic.php?f=23&t=1666

Requirements:
            VapourSynth R27 or newer
     Plugins:
  					EEDI2						
						nnedi3						
						RemoveGrain/Repair			
						fmtconv						
						GenericFilters				
						MSmoosh						
						MVTools						
						TemporalSoften			
						sangnom
		  Script:
						HAvsFunc r18 or newer (and its requirements)
						mvsfunc r2 or newer (and its requirements)

And you should know THIS:

Only YUV colorfmaily is supported! And input bitdepth must be 8 or 16 !
Output is always 16bit.
"aatype" = -2 and 2 are DISABLED by default because of eedi3 bugs.
(Will be enabled when VS R28 released, if you complied EEDI3.dll yourself, use "ignore=True" to enable these aatype)
"mtype" and "mtype2" = 5 are DISABLED.
