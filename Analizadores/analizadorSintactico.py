import csv
import ply.lex as lex
from AnalizadorLexico import analyze_file

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

def parser_ll1(token_objects_list, parsing_table, start_symbol='Program'): 
    eof_token = lex.LexToken()
    eof_token.type = '$'
    eof_token.value = '$'
    eof_token.lineno = 0 
    eof_token.lexpos = 0 
    tokens_for_parsing = token_objects_list + [eof_token]
    index = 0

    raiz = Nodo(start_symbol) 
    stack = [('$', None), (start_symbol, raiz)]

    ancho_stack = 50
    ancho_input = 50
    ancho_action = 40

    print("\n" + "="*(ancho_stack + ancho_input + ancho_action + 6))
    print(f"{'Stack':<{ancho_stack}} | {'Input Token (Type, Value, Line)':<{ancho_input}} | {'Action':<{ancho_action}}")
    print("-"*(ancho_stack + ancho_input + ancho_action + 6))

    while stack:
        top_grammar_symbol, current_node_in_tree = stack.pop() 
        
        current_token_object = tokens_for_parsing[index]
        current_token_type_from_lexer = current_token_object.type

        stack_str = ' '.join([s[0] for s in stack + [(top_grammar_symbol, current_node_in_tree)]]) 
        
        input_token_display = f"{current_token_type_from_lexer} ({current_token_object.value}, L{current_token_object.lineno})"
        input_token_display = input_token_display[:ancho_input-3] + '...' if len(input_token_display) > ancho_input-3 else input_token_display
        
        print(f"{stack_str:<{ancho_stack}} | {input_token_display:<{ancho_input}} | ", end='')

        if top_grammar_symbol == 'epsilon': 
            print("ε (Producción vacía)")
            continue
        elif top_grammar_symbol == current_token_type_from_lexer: 
            print(f"Match: {current_token_type_from_lexer}")
            index += 1
        elif top_grammar_symbol in parsing_table: 
            rule_body = parsing_table[top_grammar_symbol].get(current_token_type_from_lexer)
            
            if rule_body:
                production_str = ' '.join(rule_body)
                print(f"{top_grammar_symbol} → {production_str}")

                child_nodes_for_stack = []
                for grammar_symbol_in_rule in reversed(rule_body):
                    if grammar_symbol_in_rule != 'epsilon':
                        child_node = Nodo(grammar_symbol_in_rule)
                        child_nodes_for_stack.append((grammar_symbol_in_rule, child_node))
                
                for _, child_n in reversed(child_nodes_for_stack):
                     current_node_in_tree.agregar_hijo(child_n)
                
                for symbol_for_stack, node_for_stack in child_nodes_for_stack:
                    stack.append((symbol_for_stack, node_for_stack))
            else:
                print(f"\n❌ Error Sintáctico: No hay regla para ({top_grammar_symbol}, {current_token_type_from_lexer}) en la línea {current_token_object.lineno}")
                print(f"Token problemático: valor='{current_token_object.value}', tipo='{current_token_object.type}'")
                print("="*(ancho_stack + ancho_input + ancho_action + 6))
                return None
        else:
            print(f"\n❌ Error Sintáctico: Se esperaba '{top_grammar_symbol}' pero se encontró '{current_token_type_from_lexer}' (valor: '{current_token_object.value}') en la línea {current_token_object.lineno}")
            print("="*(ancho_stack + ancho_input + ancho_action + 6))
            return None

        if top_grammar_symbol == '$' and current_token_type_from_lexer == '$':
            print("-"*(ancho_stack + ancho_input + ancho_action + 6))
            print(f"{'$':<{ancho_stack}} | {'$':<{ancho_input}} | ACEPTADO")
            print("="*(ancho_stack + ancho_input + ancho_action + 6))
            return raiz

    print("\n❌ Error Sintáctico: Entrada incompleta o pila vacía inesperadamente.")
    print("="*(ancho_stack + ancho_input + ancho_action + 6))
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

if __name__ == '__main__':
    tabla_parsing = cargar_tabla_desde_csv("E:\\Compiladores\\Gramática\\tablitaTransiciones2.csv")
    
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input4.ws" 

    print(f"--- Analizando léxicamente el archivo: {archivo_entrada_path} ---")
    lista_de_tokens = analyze_file(archivo_entrada_path) 

    if lista_de_tokens:
        print(f"--- Tokens generados por el lexer: ---")
        for tok in lista_de_tokens:
            print(tok)
        print(f"--- Iniciando análisis sintáctico ---")
        arbol_sintactico = parser_ll1(lista_de_tokens, tabla_parsing, start_symbol='Program')

        if arbol_sintactico:
            print("\n✅ Entrada aceptada por el analizador sintáctico.")
            
            print("\nÁrbol sintáctico en preorder (nodos de gramática):")
            arbol_sintactico.imprimir_preorden()
            
            print("\n\nEstructura del árbol sintáctico:")
            imprimir_arbol(arbol_sintactico)

            exportar_arbol_a_graphviz(arbol_sintactico, "E:\\Compiladores\\Salida Graphviz\\arbol_parseo.txt")
        else:
            print("\n❌ Entrada rechazada por el analizador sintáctico.")
    else:
        print("\n❌ Error durante el análisis léxico o el archivo no contiene tokens.")