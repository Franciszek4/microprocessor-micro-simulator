from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5.uic import loadUi
import sys
from PyQt5.QtCore import Qt, QRect, QSize
from PyQt5.QtWidgets import QWidget, QPlainTextEdit, QTextEdit
from PyQt5.QtGui import QColor, QPainter, QTextFormat, QTextCursor
import win32api
from time import sleep
import os

class Window(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = loadUi('untitled.ui',self)
        self.ui.run_btn.clicked.connect(self.button_action)
        self.ui.step_btn.clicked.connect(self.button_action)
        self.setWindowTitle("Microprocesor simulator")
        self.interruptions = ['int10h', 'int13h', 'int15h', 'int16h', 'int1ah', 'int21h']
        self.available_commands = ['mov', 'add', 'sub']
        self.available_registers = ['ax', 'bx', 'cx', 'dx', 'ah', 'bh', 'ch', 'dh', 'al', 'bl', 'cl', 'dl']
        self.registers_values = [0, 0, 0, 0]
        self.command = None
        self.register = None
        self.operand = None
        self.register_index = None
        self.source_register = None
        self.line_index = 0
        self.line_from_editor = None
        self.string_lenght = 0
        self.ui.actionOpen.triggered.connect(self.open_file)
        self.ui.actionOpen.setShortcut("Ctrl+O")
        self.ui.actionSave.triggered.connect(self.save_file)
        self.ui.actionSave.setShortcut("Ctrl+S")
        self.command_to_execute = False
        self.int_func_idx = None
        self.int_idx = None
        self.stack = [0, 0, 0, 0, 0, 0, 0, 0]
        self.stack_index = 7
        self.error = False
        # self.ui.editor.cursorPositionChanged.connect(self.highlightCurrentLine)
        self.update_registers()
        self.update_stack()

    def stack_service(self):
        self.register_index = self.available_registers.index(self.register)
        temp_index = self.register_index
        self.check_index()
        if self.command == 'push':

            if self.stack_index == 0 and self.stack[self.stack_index] != 0:
                self.error = True
            else:
                if temp_index > 7:
                    register_value = self.registers_values[self.register_index] % 256
                elif temp_index > 3:
                    register_value = self.registers_values[self.register_index] // 256
                else:
                    register_value = self.registers_values[self.register_index]

                self.stack[self.stack_index] = register_value

                if self.stack_index == 0:
                    self.stack_index = 0
                else:
                    self.stack_index -= 1

        elif self.command == 'pop':
            if self.stack_index != 7 and self.stack_index != 0:
                self.stack_index += 1
                if temp_index > 7:
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = temp_h * 256 + self.stack[self.stack_index] % 256
                elif temp_index > 3:
                    temp_l = self.registers_values[self.register_index] % 256
                    self.registers_values[self.register_index] = temp_l + self.stack[self.stack_index] % 256 * 256
                else:
                    self.registers_values[self.register_index] = self.stack[self.stack_index]
            else:
                self.error = True
            if self.stack_index == 0:
                self.stack_index += 1
            self.stack[self.stack_index] = 0


        self.update_stack()
        self.update_registers()

    def write_func_idx(self):
        temp_l = self.registers_values[0] % 256
        self.registers_values[0] = self.operand * 256 + temp_l
        self.update_registers()

    def interruption_service(self):
        self.int_idx = self.interruptions.index(self.command)
        if self.int_idx == 0:
            self.int10h()
        elif self.int_idx == 1:
            self.int13h()
        elif self.int_idx == 2:
            self.int15h()
        elif self.int_idx == 3:
            self.int16h()
        elif self.int_idx == 4:
            self.int1ah()
        elif self.int_idx == 5:
            self.int21h()
        self.update_registers()

    def int10h(self):
        func_idx = self.registers_values[0] // 256
        if func_idx == 0x02:
            self.set_cursor()
        elif func_idx == 0x06:
            self.scroll_up()
        elif func_idx == 0x07:
            self.scroll_down()

    def int13h(self):
        pass

    def int15h(self):
        func_idx = self.registers_values[0] // 256
        if func_idx == 0x86:
            self.wait()

    def int16h(self):
        func_idx = self.registers_values[0] // 256
        if func_idx == 0x00:
            self.read_character()

    def int1ah(self):
        func_idx = self.registers_values[0] // 256
        if func_idx == 0x02:
            self.read_time()
        elif func_idx == 0x03:
            self.set_time()
        elif func_idx == 0x04:
            self.read_date()
        elif func_idx == 0x05:
            self.set_date()

    def int21h(self):
        func_idx = self.registers_values[0] // 256
        if func_idx == 0x00:
            self.close_program()
        if func_idx == 0x02:
            self.write_char()
        if func_idx == 0x47:
            self.current_dir()

    def current_dir(self):
        path = os.getcwd()
        print(path)

    def write_char(self):
        ascii_char = self.registers_values[3] % 256
        self.ui.output_line.setText(chr(ascii_char))
        # print(chr(ascii_char))

    def close_program(self):
        sys.exit()

    def scroll_up(self):
        lines_to_scroll = self.registers_values[0] % 256
        for i in range(0, lines_to_scroll):
            self.ui.editor.moveCursor(QTextCursor.Up)

    def scroll_down(self):
        lines_to_scroll = self.registers_values[0] % 256
        for i in range(0, lines_to_scroll):
            self.ui.editor.moveCursor(QTextCursor.Down)

    def wait(self):
        high_word = self.registers_values[2]
        low_word = self.registers_values[3]
        wait_time = 65536 * high_word + low_word
        sleep(wait_time / 1000000)

    def set_cursor(self):
        row = self.registers_values[3] // 256
        column = self.registers_values[3] % 256
        self.ui.editor.moveCursor(QTextCursor.Start)
        for i in range(0, row):
            self.ui.editor.moveCursor(QTextCursor.Down)
        for i in range(0, column):
            self.ui.editor.moveCursor(QTextCursor.Right)

    def read_character(self):
        #x = sys.stdin.read(1)
        x = self.ui.output_line.text()
        char = x.strip()
        char = char[0][:1]
        temp_h = self.registers_values[0] // 256
        self.registers_values[0] = temp_h * 256 + ord(char)
        self.ui.output_line.clear()

    def set_time(self):
        win32api.SetSystemTime()
        pass

    def read_time(self):
        data = win32api.GetSystemTime()
        hours = int(data[4])
        minutes = int(data[5])
        seconds = int(data[6])
        self.registers_values[2] = hours * 256 + minutes
        temp_l = self.registers_values[3] % 256
        self.registers_values[3] = seconds * 256 + temp_l

    def set_date(self):
        pass

    def read_date(self):
        data = win32api.GetSystemTime()
        print(data)
        year_high = int(data[0] // 100)
        year_low = int(data[0] % 100)
        month = int(data[1])
        day = int(data[3])
        self.registers_values[2] = year_high * 256 + year_low
        self.registers_values[3] = month * 256 + day

    def open_file(self):
        name = QFileDialog.getOpenFileName()
        try:
            file = open(name[0], 'r')
            with file:
                text = file.read()
                self.editor.setText(text)
        except:
            pass

    def save_file(self):
        text = self.editor.toPlainText()
        name = QFileDialog.getSaveFileName()
        if name:
            file = open(name[0], 'w')
            with file:
                file.write(text)

    def read_command(self):
        input = self.line_from_editor
        input = input.lower()
        input = input.split()
        self.command = input[0]

        if len(input) > 1:
            self.register = input[1]

        if self.command in self.interruptions:
            self.interruption_service()
        elif self.command in ['push', 'pop'] and self.register in self.available_registers:
            self.stack_service()
        elif self.register in self.available_registers:
            try:
                self.operand = int(input[2])
                self.command_to_execute = True
            except ValueError:
                if input[2] in self.available_registers:
                    self.operand = input[2]
                    self.source_register = self.available_registers.index(self.operand)
                    self.command_to_execute = True
                elif self.register == 'ah':
                    self.operand = input[2]
                    self.operand = self.operand.replace('h', '')
                    try:
                        self.operand = int(self.operand, base=16)
                        self.write_func_idx()
                    except:
                        pass
                    self.command_to_execute = False
            if self.command in self.available_commands and self.register in self.available_registers and self.command_to_execute:
                try:
                    self.execute_command()
                except:
                    self.ui.output_line.setText('Błąd1 !')
        else:
            self.ui.output_line.setText('Błąd2 !')

    def execute_command(self):
        self.register_index = self.available_registers.index(self.register)
        tmp_index = self.register_index
        tmp_source = self.source_register
        self.check_index()
        if self.source_register is None:
            if self.command == 'mov':
                if tmp_index > 7 and self.operand < 256:
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = self.operand + temp_h*256
                elif tmp_index > 3 and self.operand < 256:
                    temp_l = self.registers_values[self.register_index] % 256
                    self.registers_values[self.register_index] = self.operand*256 + temp_l
                elif self.operand < 65536:
                    self.registers_values[self.register_index] = self.operand
            if self.command == 'add':
                if tmp_index > 7 and self.operand < 256:
                    self.registers_values[self.register_index] += self.operand
                elif tmp_index > 3 and self.operand < 256:
                    temp_l = self.registers_values[self.register_index] % 256
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = temp_h*256 + self.operand*256 + temp_l
                elif self.operand < 65536:
                    self.registers_values[self.register_index] += self.operand
            if self.command == 'sub':
                if tmp_index > 7 and self.operand < 256:
                    self.registers_values[self.register_index] -= self.operand
                elif tmp_index > 3 and self.operand < 256:
                    temp_l = self.registers_values[self.register_index] % 256
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = temp_h*256 - self.operand*256 + temp_l
                elif self.operand < 65536:
                    self.registers_values[self.register_index] -= self.operand
        else:
            if self.command == 'mov':
                if tmp_index > 7 and tmp_source > 7:
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = self.registers_values[self.source_register] % 256 + temp_h * 256
                elif tmp_index > 7 and tmp_source > 3:
                    temp_h = self.registers_values[self.register_index] // 256
                    self.registers_values[self.register_index] = self.registers_values[self.source_register] // 256  + temp_h * 256
                elif tmp_index > 3 and tmp_source > 7:
                    temp_l = self.registers_values[self.register_index] % 256
                    self.registers_values[self.register_index] = self.registers_values[self.source_register] % 256 * 256 + temp_l
                else:
                    self.registers_values[self.register_index] = self.registers_values[self.source_register]
            if self.command == 'add':
                if tmp_index > 7 and tmp_source > 7:
                    self.registers_values[self.register_index] += self.registers_values[self.source_register] % 256
                elif tmp_index > 7 and tmp_source > 3:
                    self.registers_values[self.register_index] += self.registers_values[self.source_register] // 256
                elif tmp_index > 3 and tmp_source > 7:
                    self.registers_values[self.register_index] += self.registers_values[self.source_register] % 256 * 256
                else:
                    self.registers_values[self.register_index] += self.registers_values[self.source_register]
            if self.command == 'sub':
                if tmp_index > 7 and tmp_source > 7:
                    self.registers_values[self.register_index] -= self.registers_values[self.source_register] % 256
                elif tmp_index > 7 and tmp_source > 3:
                    self.registers_values[self.register_index] -= self.registers_values[self.source_register] // 256
                elif tmp_index > 3 and tmp_source > 7:
                    self.registers_values[self.register_index] -= self.registers_values[self.source_register] % 256 * 256
                else:
                    self.registers_values[self.register_index] -= self.registers_values[self.source_register]
        self.command_to_execute = False
        self.update_registers()

    def update_registers(self):
        self.ui.ah_line.setText(str(self.registers_values[0] // 256))
        self.ui.al_line.setText(str(self.registers_values[0] % 256))
        self.ui.bh_line.setText(str(self.registers_values[1] // 256))
        self.ui.bl_line.setText(str(self.registers_values[1] % 256))
        self.ui.ch_line.setText(str(self.registers_values[2] // 256))
        self.ui.cl_line.setText(str(self.registers_values[2] % 256))
        self.ui.dh_line.setText(str(self.registers_values[3] // 256))
        self.ui.dl_line.setText(str(self.registers_values[3] % 256))

    def update_stack(self):
        self.ui.stack7.setText(str(self.stack[7]))
        self.ui.stack6.setText(str(self.stack[6]))
        self.ui.stack5.setText(str(self.stack[5]))
        self.ui.stack4.setText(str(self.stack[4]))
        self.ui.stack3.setText(str(self.stack[3]))
        self.ui.stack2.setText(str(self.stack[2]))
        self.ui.stack1.setText(str(self.stack[1]))
        self.ui.stack0.setText(str(self.stack[0]))

    def button_action(self):
        sender = self.sender()
        if sender.text() == 'Run':
            self.run_program()
        elif sender.text() == 'Step':
            self.run_program_step()

    def run_program(self):
        program = self.ui.editor.toPlainText()
        program = program.replace(',', ' ')
        lines = program.split('\n')
        for line in lines:
            self.line_from_editor = line
            self.read_command()

    def highlightCurrentLine(self):
        extraSelections = []

        if not self.ui.editor.isReadOnly():
            selection = self.ui.editor.ExtraSelection()
            if not self.error:
                lineColor = QColor(Qt.yellow).lighter(160)
            else:
                lineColor = QColor(Qt.red).lighter(160)
                self.error = False
            selection.format.setBackground(lineColor)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.ui.editor.textCursor()
            selection.cursor.clearSelection()
            extraSelections.append(selection)
        self.ui.editor.setExtraSelections(extraSelections)

    def run_program_step(self):
        program = self.ui.editor.toPlainText()
        program = program.replace(',', ' ')
        lines = program.split('\n')
        if self.line_index < len(lines):
            self.ui.editor.moveCursor(QTextCursor.Start)
            for i in range(0, self.line_index):
                self.ui.editor.moveCursor(QTextCursor.Down)
            self.line_from_editor = lines[self.line_index]
            self.read_command()
            self.highlightCurrentLine()
            self.line_index += 1
            if self.line_index == len(lines):
                self.line_index = 0

    def check_index(self):
        if self.register_index > 7:
            self.register_index -= 8
        elif self.register_index > 3:
            self.register_index -= 4
        if self.source_register is not None:
            if self.source_register > 7:
                self.source_register -= 8
            elif self.source_register > 3:
                self.source_register -= 4


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main = Window()
    main.show()
    sys.exit(app.exec_())