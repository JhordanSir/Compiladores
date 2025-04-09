import csv

def cargar_tabla_desde_csv(nombre_archivo):
    tabla = {}
    with open(nombre_archivo, newline='') as csvfile:
        reader = csv.reader(csvfile)
        encabezado = next(reader)[1:]  # Saltamos la columna vacía inicial

        for fila in reader:
            no_terminal = fila[0].strip()
            tabla[no_terminal] = {}
            for terminal, celda in zip(encabezado, fila[1:]):
                produccion = celda.strip()
                if produccion:
                    tabla[no_terminal][terminal.strip()] = produccion.split()
    return tabla

def parser_ll1(input_string, parsing_table):
    tokens = input_string.split() + ['$']
    stack = ['$', 'E']
    index = 0

    print(f"{'Stack':<25}{'Input':<25}{'Action'}")

    while True:
        if not stack:
            break

        top = stack.pop()
        current_token = tokens[index] if index < len(tokens) else None

        stack_str = ' '.join(reversed(stack + [top]))
        input_str = ' '.join(tokens[index:])
        print(f"{stack_str:<25}{input_str:<25}", end='')

        if top == 'epsilon':
            print("ε")
            continue
        elif top == current_token:
            print("terminal")
            index += 1
        elif top in parsing_table:
            rule = parsing_table[top].get(current_token)
            if rule:
                production = ' '.join(rule)
                print(f"{top} → {production}")
                for symbol in reversed(rule):
                    if symbol != 'epsilon':
                        stack.append(symbol)
            else:
                print(f"\n❌ Error: no rule for ({top}, {current_token})")
                return False
        else:
            print(f"\n❌ Error: unexpected symbol '{top}'")
            return False

        if top == '$' and current_token == '$':
            print(f"{'$':<25}{'$':<25}ACCEPT")
            return True

    print("\n❌ Entrada incompleta o mal formada")
    return False

# Cargar tabla desde archivo CSV
tabla = cargar_tabla_desde_csv("E:\\Compiladores\\Analizador sintáctico (bottom-up)\\tablita.csv")

# Probar con una entrada válida
entrada = "int ++ int"
if parser_ll1(entrada, tabla):
    print("\n✅ Entrada aceptada")
else:
    print("\n❌ Entrada rechazada")
