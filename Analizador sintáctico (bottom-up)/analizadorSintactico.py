import csv

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.hijos = []

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)

    def imprimir_preorden(self):
        print(self.valor, end=', ')
        for hijo in self.hijos:
            hijo.imprimir_preorden()

def imprimir_arbol(nodo, nivel=0, prefijo='', es_ultimo=True):
    
    espacio = '    '
    rama = '│   '
    rama_esquina = '└── '
    rama_t = '|── '
    
    conector = rama_esquina if es_ultimo else rama_t
    
    if nivel > 0:
        print(f"{prefijo}{conector}{nodo.valor}")
    else:
        print(f"{espacio}{nodo.valor}") 

    nuevo_prefijo = prefijo + (espacio if es_ultimo else rama)
    
    num_hijos = len(nodo.hijos)
    for i, hijo in enumerate(nodo.hijos):
        imprimir_arbol(hijo, nivel + 1, nuevo_prefijo, i == num_hijos - 1)

def cargar_tabla_desde_csv(nombre_archivo):
    tabla = {}
    with open(nombre_archivo, newline='') as csvfile:
        reader = csv.reader(csvfile)
        encabezado = next(reader)[1:]

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
    index = 0
    
    raiz = Nodo('E')
    stack = [('$', None), ('E', raiz)] 

    print(f"{'Stack':<25}{'Input':<25}{'Action'}")

    while stack:
        top_symbol, top_node = stack.pop()
        current_token = tokens[index]

        stack_str = ' '.join([s[0] for s in stack + [(top_symbol, top_node)]])
        input_str = ' '.join(tokens[index:])
        print(f"{stack_str:<25}{input_str:<25}", end='')

        if top_symbol == 'epsilon':
            print("ε")
            continue
        elif top_symbol == current_token:
            print("terminal")
            index += 1 
        elif top_symbol in parsing_table:
            rule = parsing_table[top_symbol].get(current_token)
            if rule:
                production = ' '.join(rule)
                print(f"{top_symbol} → {production}") 

                child_nodes = []
                for symbol in rule:
                    child = Nodo(symbol)
                    top_node.agregar_hijo(child)
                    
                    if symbol != 'epsilon':
                        child_nodes.append((symbol, child))
                
                for symbol_node in reversed(child_nodes):
                    stack.append(symbol_node)
            else:
                print(f"\n❌ Error: no rule for ({top_symbol}, {current_token})")
                return None
        else:
            print(f"\n❌ Error: unexpected symbol '{top_symbol}'")
            return None

        if top_symbol == '$' and current_token == '$':
            print(f"{'$':<25}{'$':<25}ACCEPT")
            return raiz 

    print("\n❌ Entrada incompleta o mal formada")
    return None 

def generar_graphviz(nodo, archivo, contador=[0], conexiones=[]):
    id_actual = contador[0]
    archivo.write(f'  node{id_actual} [label="{nodo.valor}"];\n')
    nodo_id = id_actual
    contador[0] += 1
    for hijo in nodo.hijos:
        hijo_id = contador[0]
        conexiones.append((nodo_id, hijo_id))
        generar_graphviz(hijo, archivo, contador, conexiones)
    return conexiones

def exportar_arbol_a_graphviz(raiz, nombre_archivo="arbol.txt"):
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write("digraph G {\n")
        conexiones = []
        generar_graphviz(raiz, archivo, [0], conexiones)
        for origen, destino in conexiones:
            archivo.write(f"  node{origen} -> node{destino};\n")
        archivo.write("}\n")

tabla = cargar_tabla_desde_csv("tablita.csv")

entrada = "( int + int )"

arbol = parser_ll1(entrada, tabla)

if arbol:
    print("\n✅ Entrada aceptada")
    
    print("\nÁrbol sintáctico en preorder:")
    arbol.imprimir_preorden()
    
    print("\n\nEstructura del árbol sintáctico:")
    imprimir_arbol(arbol)

    exportar_arbol_a_graphviz(arbol, "arbol.txt")
else:
    print("\n❌ Entrada rechazada")