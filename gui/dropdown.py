import PySimpleGUI as sg

words = ['apple', 'banana', 'cherry', 'date',
         'elderberry', 'fig', 'grape', 'honeydew']

layout = [
    [sg.Input(key='-INPUT-')],
    [sg.Listbox(values=words, size=(20, 6), key='-LIST-')],
]

window = sg.Window('Filtering Dropdown', layout)

while True:
    event, values = window.read()
    print(event , values)

    if event == sg.WIN_CLOSED:
        break

    input_text = values['-INPUT-'].lower()  # Convert input to lowercase
    filtered_words = [word for word in words if input_text in word.lower()]

    window['-LIST-'].update(values=filtered_words)

window.close()
