; -------- EBS --------
START_EBS:
    ;Berechne Ablenkpositionen

    _lges=SQRT(POT(_ZielPosX-_StrtPosX)+POT(_ZielPosY-_StrtPosY))

    _Phi=ATAN2((_ZielPosY-_StrtPosY),(_ZielPosX-_StrtPosX)) ;Winkel
    ;Ende Upslope
    _UpX=_StrtPosX+(_lUp*cos(_Phi))
    _UpY=_StrtPosY+(_lUp*sin(_Phi))               
    ;Beginn Downslope
    _DwnX=_ZielPosX-(_lDwn*cos(_Phi))
    _DwnY=_ZielPosY-(_lDwn*sin(_Phi))

    ;Beginn Vorlauf
    _VorX=_StrtPosX-(_lVor*cos(_Phi))               ;X
    _VorY=_StrtPosY-(_lVor*sin(_Phi))               ;Y bzw. Z
    ;Ende Nachlauf
    _NachX=_ZielPosX+(_lNach*cos(_Phi))               ;X
    _NachY=_ZielPosY+(_lNach*sin(_Phi))               ;Y bzw. Z

    --> Hier FuGen einfügen
    --> ggf. Pulsen einschalten

    M0


    G1 G90 G64
    X=_StrtPosX Y=_StrtPosX Fms _Fp   ;Anfahren Startpunkt
    X=_VorX Y=_VorY Fms _Fs           ;zum Vorlauf
    X=_StrtPosX Y=_StrtPosY           ;zu Beginn Upslope
    X=_UpX Y=_UpY SQ SQs) SL _SLs) ;Upsl.
    X=_DwnX Y=_DwnY          ;Schweissen
    X=_ZielPosX Y=_ZielPosY SQ 0) Sl (_SLs+300)) ;Downsl.
    X=_NachX Y=_NachY           ;Nachlauf
    X=_ZielPosX Y=_ZielPosY          ;Endpunkt f. Kontrolle

    WRT(S_FIG,6, S_SWX,40, S_SWY, 40, S_FRQ, 1000)
    SNS

    --> FuGen AUS
    --> ggf. Pulsen AUS

END_EBS:



--------------------------------------------------------------------

 zu definieren:
    ohne Parameter
        lges, phi, upX, upY, DwnX, DwnY, VorX, VorY, NachX, NachY, 
  
    mit Parameter
        SLoff, lUp, lDwn, lVor, lNach, versatz

nicht definieren, aber parametrieren: 
    SQs, Fs, SLs, SLo, SLs  



 