# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 11:15:32 2018

Template zum Darstellen von .ui-Dateien, die mit QT designed wurden


test

@author: halbauer
"""


from PyQt5 import QtCore, QtGui, QtWidgets
from functools import partial
import sys 
from PyQt5 import uic
import numpy as np
import re
import json
from os.path import isdir, dirname


design_file = 'src/gui_mumo_gen.ui'      # <-- Insert Python File of UI
pop_up = 'src/para-dia.ui'
comments = 'src/comments.ui'
preview = 'src/textviewer.ui'

MainWindow = uic.loadUiType(design_file)[0]
ParaDialog = uic.loadUiType(pop_up)[0]   # lädt nur die Klasse des Designs
CommentDialog = uic.loadUiType(comments)[0]
Preview = uic.loadUiType(preview)[0]

class Singleton:
    """Alex Martelli implementation of Singleton (Borg)
    http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    Hier wird ein Dictionary instanziert, das man klassenübergreifend beschreiben kann
    """
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class Database(Singleton):
    def __init__(self):
        Singleton.__init__(self)

    def get(self):
        return self._data

    def change(self, *args):
        for arg in args:
            self._data.update(arg)
    
    def append(self, key, args, key2=None):
        if not key2:
            for arg in args:
                self._data[key].append(arg)
        elif not isinstance(args, list):
            self._data[key][key2].append(args)
        else:
            for arg in args:
                self._data[key][key2].append(args)

    def reset(self, *args):
        for key in args:
            try:
                del self._data[key]
            except KeyError:
                print(f'Das Schlüsselwort {key} wurde nicht gefunden!')

    def hasData(self):
        return hasattr(self, "_data")

    def clear(self):
        self._data = {}

    def load(self):
        '''
        Kommentar:
            Dieses Feld enthält Kommentare zum Programm.
            Jedes Element entspricht einer Zeile.
            Geschrieben werden nur die Kommentarstrings.
            Beim Schreiben der CNC-Datei wird dann ein Semikolon angefügt. 
        Definitionen:
            Es werden nur die Variablennamen angegeben, die definiert werden müssen. 
            Den Variablen muss ein Typ zugeordnet werden. 
            Dafür muss bei der Übergabe der Daten gecheckt werden, ob diese Variablen in der Pro-beam Liste definiert sind.
            Schnelle Lösung: Bei der Eingabe der Daten gibt es eine Spalte "TYP", in die der Typ eingefügt werden muss.
            Bei vordefinierten Variablen ist keine Angabe erforderlich.
            Wenn die Daten geparst werden, muss geprüft werden, ob die Zeilenlänge über den Bildschirmrand reicht.
            Anschließend muss ein "DEF" vor die Zeilen gesetzt werden. 
        '''
        
        self._data = {
            'Comment': {
                'Autor' : 'Halbauer',
                'Datum' : '01.01.2020',
                'Hochspannung': '80 kV'
            },
            'Definitionen': {
                'INT' : [],
                'REAL': [],
                'CHAR': [], 
                'BOOL': [],
                'EXTERN': []
            }, 
            'Schalter': [
                'VORPOS', 'ELO', 'EBS'
            ],
            'Variablen':[
                ['INT', 'KALWERT', '2255', 'Kalibrierwert', '-'],  
            ]
        }


class MyApp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MyApp, self).__init__(parent)
        self.ui = MainWindow()
        self.ui.setupUi(self)
        self.setup_triggers()   # lade Events für Buttons
        db = Database()
        db.load()
        # db = Database()
        # db.load()
        # print(db.get())
        # para = {
        #     'Definitionen': 
        #     {
        #         'Variablen': ['_SWXg', '_Kalwert']
        #     }
        # }
        # db.change(para)
        # print(db.get())
        # db.reset('Definitionen')
        # print(db.get())

    def setup_triggers(self):
        self.ui.but_test_print.clicked.connect(self.get_mumo_data)
        self.ui.but_write_cnc.clicked.connect(self.write_mpf)
        self.ui.rad_but_mumo.toggled.connect(self.onClicked)
        self.ui.rad_but_mimo.toggled.connect(self.onClicked)
        self.ui.but_cnc_para.clicked.connect(self.openParaView)
        self.ui.debug.clicked.connect(self.debug)
        self.ui.but_comment.clicked.connect(self.getcomment)
        self.ui.but_cnc_preview.clicked.connect(partial(self.write_mpf, True))
        self.ui.but_updateDB.clicked.connect(self.update_db)
        self.ui.actionSave.triggered.connect(self.export_db)
        self.ui.actionLoad.triggered.connect(self.read_from_json)

    def preview_cnc(self, text):
        self.prev = CNCPreview(text)
        self.prev.show()

    def debug(self):
        '''
            Diese Funktion wird nur fürs debugging benutzt. 
            Hier kommen alle Befehle rein, die getestet werden sollen.
        '''
        db = Database()
        # db.load()
        print(db.get())

    def getcomment(self):
        self.cd = Comments()
        self.cd.show()

    def get_geo(self):
        '''
        Diese Funktion schaut, wie groß der Bildschirm ist, auf dem die App ausgeführt wird.
        Und gibt an, wie groß die App ist, auf der sie ausgeführt wird. 
        '''
        ag = QtWidgets.QDesktopWidget().availableGeometry()
        sg = QtWidgets.QDesktopWidget().screenGeometry()
        wg = self.geometry()
        return ag, sg, wg

    def openParaView(self):
        self.pop = PopUp()
        self.setGeo()
        self.pop.show()

    def setGeo(self):
        ag, _, wg = self.get_geo()
        # Hole Geometrie des Hauptfensters und des Monitors ab
        # Schaue nach Geometrie des PopUps
        p_geo = self.pop.geometry()

        # Wenn Fenster rechts nicht mehr hinpasst
        if ((wg.x() + wg.width()) - p_geo.width()) < ag.width():
            x_pos = wg.x() + wg.width()
        # Setze es auf die Linke Seite
        else: 
            x_pos = wg.x() - p_geo.width()
        
        y_pos = wg.y()

        self.pop.setGeometry(x_pos, y_pos, p_geo.width(), wg.height())

    def onClicked(self):
        rb = self.sender()
        if rb.text() == 'MultiMode':
            self.ui.minimod_para.setEnabled(False)
            self.ui.multimode_para.setEnabled(True)
        if rb.text() == 'MiniMode':
            self.ui.multimode_para.setEnabled(False)
            self.ui.minimod_para.setEnabled(True)
               
    def print_to_line(self):
        text = self.ui.tab_gen.item(1, 1).text()
        self.ui.testout.setText(text)

    def get_item(self, row, col):
        return self.ui.tab_gen.item(row, col)

    def get_mumo_data(self):
        # Daten werden initialisiert
        # TODO: nicht bei jedem Aufruf starten,
        # sondern nur geänderte Werte übernehmen
        anz_c = self.ui.tab_gen.columnCount()
        data = []
        # [i] for i in range(anz_r)
        # Generatorreihenfolge wird eingelesen
        gen_order = self.ui.txt_gen_order.text()
        # Der String wird an den Leerzeichen aufgespalten und einem Array übergeben
        rows = [int(x) for x in gen_order.split()]
        # Generatoren werden ohne Wiederholung behandelt
        # (keine Mehrfachbeschreibung der Daten)
        rows_uni = np.unique(rows)
        # Datenlabels werden erzeugt
        # keys = ['INDEX ', 'FIG ', 'SWX ', 'SWY ', 'DCx ', 'DCy ', 'DCz ',
                # 'SLC ', 'PVZ ', 'VEK ']
        for row in rows_uni:
            # keys = [key + str(rows) for key in keys]
            items = [self.ui.tab_gen.item(row, col).text() for col in range(anz_c)]
            data.append(items)
        # print(self.rows_uni)
        # print(self.data)

        return data, rows

    def update_db(self):
        db = Database()

        config = {'Config': {
            'CI': self.ui.check_ci.isChecked(),
            'FLASH': self.ui.check_flash.isChecked(),
            'NAME': self.ui.txt_proz_name.text(),
            'NOXY': self.ui.check_no_xy.isChecked(),
            'XY': self.ui.check_xy.isChecked(),
            'SUSV': self.ui.check_susv.isChecked(),
            'CIRC': self.ui.check_circular.isChecked(),
            'LIN': self.ui.check_linear.isChecked(),
            'AUTOLIN': self.ui.cb_lin_auto.isChecked(),
            'REG': self.ui.check_reg.isChecked(),
            'ELO': self.ui.check_elo.isChecked(),
            'POS': self.ui.check_pos.isChecked(),
            'SIM': self.ui.check_sim.isChecked(),
            'JOG': self.ui.check_jog.isChecked(),
            'HDW': self.ui.check_hdws.isChecked(),
            'MP': self.ui.check_mp.isChecked(),
            'FUSU': self.ui.check_fusu.isChecked(),
            'MUMO': self.ui.rad_but_mumo.isChecked(),
            'MIMO': self.ui.rad_but_mimo.isChecked()
        }}

        db.change(config)

        par_ini = []
        if self.ui.rad_but_mumo.isChecked():
            par_ini.append(('REG[21]', 'INT'))
            par_ini.append(('REGDATA[20]', 'INT'))
            par_ini.append(('M_SEL[128]', 'CHAR'))
            par_ini.append(('M_SEL_CNT', 'CHAR'))
            # para_ini.append('DEF INT _REG[21]\nDEF INT _REGDATA[20]\nDEF CHAR M_SEL[128]\nDEF CHAR M_SEL_CNT\n')

        if self.ui.check_reg.isChecked():
            par_ini.append(('PYR_INIT (INT)', 'EXTERN'))
            par_ini.append(('PYR_PAR[10]', 'REAL'))
        # Schreibe Werte in die Datenbank
        # db.append('Definitionen', par_ini)
        
        self.write_definitions(par_ini)

        # Parametrieren des Funktionsgenerators
        mumo_data, gen_rows = self.get_mumo_data()

        db.change({'Funktionsgenerator': {'Parameter': mumo_data, 'Order': gen_rows}})

    def export_db(self):
        db = Database()
        data = db.get()

        files_types = "JSON (*.json)"
        path = QtWidgets.QFileDialog.getSaveFileName(self, 'Datenbank speichern', "db.json", files_types)[0]

        if not isdir(dirname(path)):
            self.statusBar().showMessage('Ungültiges Verzeichnis', 2000)
            return 

        with open(path, 'w') as json_file:
            json.dump(data, json_file)

        self.statusBar().showMessage('Datenbank erfolgreich exportiert', 2000)

    def read_from_json(self):
        path = QtWidgets.QFileDialog.getOpenFileName(self, 'Datei öffnen', '.', 'JSON (*.json)')[0]
        if not isdir(dirname(path)):
            self.statusBar().showMessage('Keine Datei geladen', 2000)
            return 
        
        db = Database()
        db.clear()   # setze die Datenbank zurück

        with open(path, 'r') as f:
            data = json.load(f)

        self.statusBar().showMessage('Datenbank erfolgreich geladen', 2000)

        db.change(data)

    def hline(self, fill='=', zl=66):
            return '; ' + fill*(zl-3) + '\n'

    def filler(self, s, fill='=', zl=66):
        len_fill = int((zl - 5 - len(s))/2)
        filler = fill * len_fill
        if len_fill %2 > 0:
            string = '; ' + filler + ' ' + s + ' ' + filler + fill+'\n'
        else:
            string = '; ' + filler + ' ' + s + ' ' + filler + '\n'
        return string

    def cnc_gen(self):
        self.update_db()

        commentstring = self.parse_comments()

        definitions = self.parse_definitions()

        filler1 = self.hline() + self.filler('START Hauptprogramm', ' ') + self.hline()

    
        filler2 = self.hline() + self.filler('ENDE Hauptprogramm', ' ') + self.hline()

        fu_gen_start = self.parse_fun_gen()

        # Ende des Multigenerators
        end_par = 'MG_PAR(0)\nM02'

        cnc_code = [commentstring, definitions, filler1, filler2, fu_gen_start, end_par]

        return '\n'.join(cnc_code)

    def write_definitions(self, l):
        db = Database()
        data = db.get()
        for pi in l:
            # pi[0] = Wert, pi[1] = Kategorie
            if pi[0] not in data['Definitionen'][pi[1]]: 
                db.append('Definitionen', pi[0], pi[1]) 

    def write_mpf(self, preview=False):
        #        print(self.header())
        # if preview:
        if preview:
            self.preview_cnc(self.cnc_gen())
        else: 
            fname = 'output.MPF'
            with open(fname, 'w') as f:
                f.write(self.cnc_gen())

    def split_stringlist(self, s, l=57):
        '''
            Funktion zum Aufteilen von Stringlisten.
            Es muss eine Liste aus Strings übergeben werden.
            Die Strings in der Liste werden so lange zusammengefügt, bis die Zeilenlänge l überschritten wird.
            Anschließend wird eine neue Liste mit zusammengefügten Strings, getrennt durch Leerzeichen erzeugt.
            Kann auch verwendet werden, um die Kommentare hinter einer Variablen auf mehrere Zeilen aufzuteilen. 
        '''
        if not isinstance(s, list):
            print('Es muss eine Liste übergeben werden.')
            return 
        if s == []:
            return

        slist = []
        strt = 0
        for i in range(len(s)):
            # Füge die Strings der Liste zusammen
            string = ' '.join(s[strt:i])
            # Wenn die Länge des zusammengesetzten Strings größer als die Zeilenlänge wird
            if len(string) > l:
                # gehe zum vorherigen Element
                i -= 1
                # Füge die Strings wieder neu zusammen
                string = ' '.join(s[strt:i])
                # Schreibe den gekürzten String in die Ausgabeliste
                slist.append(string)
                # instanziere den String neu, falls Leerzeichen übrigblieben
                string = ''
                # fange bei dem letzten Element an
                strt = i   
            
        slist.append(string)
        return slist

    def parse_definitions(self):
        db = Database()
        data = db.get()['Definitionen']
        
        deflist = []
        for key in data.keys():
            # übergebe die Einträge jedes Schlüsselworts an die Splitfunktion
            # erzeuge ggf. eine Liste mit mehreren Einträgen
            if data[key] == []:
                continue
            if key != 'EXTERN':
                # hänge an jede Variable zuerst einen Unterstrich an
                variablen = [f'_{s}' for s in data[key]]
                '''
                    Wende stringsplitting nur auf Mengen an, die potentiell die Zeilenlänge überschreiten.
                    Länge jedes Strings muss mit 2 addiert werden, da Leerzeichen und Komma angehängt werden
                    Länge des Strings müsste deshalb Zeilenlänge - 'DEF XXXX ' (66-9 = 57) überschreiten.
                '''    
                if sum([(len(s)+2) for s in variablen]) > 57:
                    substrings = self.split_stringlist(variablen)
                    # Setze vor jedes Element der Unterliste ein 'DEF'
                    substrings = [', '.join(sub) for sub in substrings]
                    substrings = [f'DEF {key} {sub}' for sub in substrings]
                    # Trenne die Zeilen mit einem Zeilenumbruch
                    s = '\n'.join(substrings)
                else:
                    substrings = ', '.join(variablen)
                    s = f'DEF {key} {substrings}'
            # Wenn Schlüsselwort 'EXTERN' ist
            else:
                substrings = [f'{key} {sub}' for sub in data[key]]
                # Trenne die Zeilen mit einem Zeilenumbruch
                s = '\n'.join(substrings)

            deflist.append(s)

        definitions = '\n'.join(deflist)
        definitions += '\n'
        return definitions

    def parse_comments(self):
        '''
            Funktion, um aus der Datenbank die Werte des Kommentars in die CNC-Datei zu schreiben.
        '''
        # Datenbank wird instanziert
        db = Database()
        data = db.get()
        # Kommentarspalte wird geladen
        co = data['Comment']

        string = []
        # Iteriere über alle Schlüsselworte der Kommentarspalte
        for key in co.keys():
            # Werte werden abgefragt und auf die Variable val geschrieben
            val = co[key]
            # Ausnahme für mehrzeilige Kommentare
            if key == 'Kommentar':
                # Aufteilen an Zeilenenden
                val = val.split('\n')
                # Beginn jeder Zeile mit Anstrich
                val = [';    - ' + v for v in val] 
                s1 = '\n'.join(val)
                # zusammenfügen des Strings
                s = f';- {key}:\n{s1}'
            else:    
                s = f';- {key}: {val}'
            string.append(s)
        
        # hänge am Ende der Kommentare einen Zeilenumbruch an (zur visuellen Trennung)
        string.append('\n')

        return '\n'.join(string)

    def parse_fun_gen(self):
        def write_mumo_para(arr):
            index = arr[0]
            fig = f'MM_FIG[{index}] = {arr[1]}'
            swx = f'MM_SWX[{index}] = {arr[2]}'
            swy = f'MM_SWY[{index}] = {arr[3]}'
            dcx = f'MM_DCX[{index}] = {arr[4]}'
            dcy = f'MM_DCY[{index}] = {arr[5]}'
            dcz = f'MM_DCZ[{index}] = {arr[6]}'
            slc = f'MM_SLC[{index}] = {arr[7]}'
            pvz = f'MM_PVZ[{index}] = {arr[8]}'
            vek = f'MM_VEK[{index}] = {arr[9]}'

            string = [fig, swx, swy, dcx, dcy, dcz, slc, pvz, vek]
            output = '\n'.join(string)
            return output

        def write_order(rows):
            s = []
            j = 0
            for i in rows:
                text = f'MM_SEL[{j}] = {i}'
                j += 1
                s.append(text)
            s.append('')
            text2 = f'M_SEL_CNT = {j}'
            s.append(text2)
            return '\n'.join(s)

        db = Database()
        data = db.get()
        fu = data['Funktionsgenerator']

        if self.ui.rad_but_mumo.isChecked():
            gen_data = [write_mumo_para(i) for i in fu['Parameter']]
            gen_out = '\n\n'.join(gen_data)

            filler3 = self.filler('Generatorreihenfolge', '-')        

            gen_order = ['\n', filler3, write_order(fu['Order'])]
            gen_order = '\n'.join(gen_order)

            # Start des Multigenerators
            start_par = 'MG_PAR(1)\nM00\n'

            return '\n'.join([gen_out, gen_order, start_par])


class PopUp(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.window = ParaDialog()
        self.window.setupUi(self)
        self.setup_triggers_pop()
        self.load_values()
    
    def setup_triggers_pop(self):
        self.window.but_ok.clicked.connect(self.press_ok)
        self.window.but_update.clicked.connect(self.press_update)
        self.window.but_close.clicked.connect(self.press_close)
    
    def load_values(self):
        db = Database()
        data = db.get()['Variablen']

        # iteriere über die Elemente der Variablen
        for row, row_el in enumerate(data):
            # iteriere über die Spalten und gib die Spaltenzahl und das Element zurück
            for col, el in enumerate(row_el):
                self.window.tab_cnc_para.item(row, col).setText(el)    

    def press_ok(self):
        self.press_update()
        self.close()

    def press_update(self):
        rows = self.window.tab_cnc_para.rowCount()
        cols = self.window.tab_cnc_para.columnCount()

        items = []
        for i in range(rows):
            item = []
            for j in range(cols):
                try: 
                    item.append(self.window.tab_cnc_para.item(i, j).text())
                except AttributeError:
                # break
                    pass
            if item == ['', '', '', '', ''] or item == []:
                break
            items.append(item)

        db = Database()
        para = {'Variablen': items}

        db.change(para)

        todefine = self.zu_definieren([(i[1], i[0]) for i in items])

        if todefine != []:
            data = db.get()
            for td in todefine:
                if td[0] not in data['Definitionen'][td[1]]: 
                    print(f'Folgende Variablen müssen zusätzlich definiert werden: {td[0]}')
                    db.append('Definitionen', td[0], td[1]) 
            

        self.statusBar().showMessage('Messwerte übertragen', 2000)


    def press_close(self):
        self.close()


    def zu_definieren(self, args):
        # Liste mit vorbelegten Variablen (als reguläre Ausdrücke, um Schriebarbeit zu sparen)
        vordefiniert = ['kalwert', 'fig', 'f[phskw]', 'frq[phskw]', 'hv', 'sd','sl[ofbhskw]', 'sq[fhskw]', 'strtpos[xy]', 'zielpos[xy]', 's[uv]f', 'sw[xy][phskfw]', 'txtstring', 'txtsize', 'txtsq', 'txtvek']
            
        todef = []

        for var, typ in args:
            results = []
            for _def in vordefiniert:
                results.append(re.fullmatch(_def, var.lower()))
            # Wenn keiner der regulären Ausdrücke passt 
            # (also wenn die Variable nicht definiert ist)
            # gebe True zurück 
            if not any(results):
                todef.append((var, typ))
                # print(f'Die Variable {var} ist noch nicht vordefiniert.')
        return todef

class Comments(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.com = CommentDialog()
        self.com.setupUi(self)
        self.setup_triggers_comment()
        self.load_values()

    def load_values(self):
        '''
            Diese Funktion prüft, ob es Daten in der Datenbank gibt, die in die Kommentarspalten eingefügt werden können.
            Das sorgt dafür, dass nach dem Srücken von "OK" alle Werte gespeichert werden und beim erneuten Öffnen des Fensters wieder zur Verfügung stehen. 
        '''
        db = Database()                 # instanziere Datenbank (zur Abfrage der Werte notwendig)
        data = db.get()['Comment']      # Lade den Block "Kommentare" aus der Datenbank
        keys = data.keys()              # Liste alle Schlüsselworte zur schnelleren Abfrage auf

        # Prüfe ob Felder in Schlüsselworten bereits definiert sind
        if 'Autor' in keys:
            self.com.txt_autor.setText(data['Autor'])
        if 'Datum' in keys:
            self.com.txt_datum.setText(data['Datum'])
        if 'Hochspannung' in keys:
            valid = ['60 kV', '80 kV']
            if data['Hochspannung'] in valid:
                self.com.cb_hv.setCurrentText(data['Hochspannung'])
            else:
                pass
        if 'Verstärker' in keys:
            valid = ['30V - Dreieck', '30V - Rechteck', '60V - Dreieck', '60V - Rechteck']
            if data['Verstärker'] in valid:
                self.com.cb_vs.setCurrentText(data['Verstärker'])
            else:
                pass
        if 'Kommentar' in keys:
            self.com.txt_kommentar.setText(data['Kommentar'])

    def setup_triggers_comment(self):
        self.com.but_box.accepted.connect(self.send_data)
        self.com.but_comment.clicked.connect(self.open_dialog)

    def send_data(self):
        autor = self.com.txt_autor.text()
        date = self.com.txt_datum.text()
        hv = self.com.cb_hv.currentText()
        vs = self.com.cb_vs.currentText()
        kommentar = self.com.txt_kommentar.toPlainText()
        
        comment_data = {
            'Autor' : autor, 
            'Datum' : date, 
            'Hochspannung': hv, 
            'Verstärker': vs, 
            'Kommentar': kommentar
            }

        # instanziere Datenbank (zum Schreiben der Datenbank notwendig)
        db = Database()
        para = {'Comment': comment_data}
        db.change(para)

        self.close()

    def open_dialog(self):
        '''
            Öffnet einen etwas größeren Texteingabedialog, damit lange Komentare leichter eingegeben werden können.
        '''
        text, ok = QtWidgets.QInputDialog.getMultiLineText(self, 'Programmkommentar', 'Schreibe hier einen Kommentar zum Programm:')
		
        if ok:
           self.com.txt_kommentar.setText(str(text)) 


class CNCPreview(QtWidgets.QWidget):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.pre = Preview()
        self.pre.setupUi(self)
        self.pre.preview.setPlainText(text)
    

def main():
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()
    form = MyApp()             # We set the form to be our ExampleApp (bsp1)
    form.show()                         # Show the form

    app.exec_()                         # and execute the app


if __name__ == '__main__':
    main()