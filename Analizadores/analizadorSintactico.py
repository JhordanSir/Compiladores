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

def parser_ll1(token_objects_list, parsing_table, start_symbol='Program'): # Añadido start_symbol
    # token_objects_list es la lista de objetos Token de AnalizadorLexico.py

    # Crear un token EOF (End Of File) para marcar el final de la entrada
    eof_token = lex.LexToken()
    eof_token.type = '$'
    eof_token.value = '$'
    eof_token.lineno = 0 # O la última línea del archivo
    eof_token.lexpos = 0 # O la última posición

    # La secuencia de tokens para el parser ahora consiste en los objetos token + EOF
    tokens_for_parsing = token_objects_list + [eof_token]
    index = 0

    raiz = Nodo(start_symbol) # Usar el símbolo inicial
    # La pila ahora almacena tuplas: (nombre_simbolo_gramatica, nodo_arbol_correspondiente)
    stack = [('$', None), (start_symbol, raiz)]

    ancho_stack = 50
    ancho_input = 50 # Aumentado para mostrar más del token actual
    ancho_action = 40

    print("\n" + "="*(ancho_stack + ancho_input + ancho_action + 6))
    print(f"{'Stack':<{ancho_stack}} | {'Input Token (Type, Value, Line)':<{ancho_input}} | {'Action':<{ancho_action}}")
    print("-"*(ancho_stack + ancho_input + ancho_action + 6))

    while stack:
        top_grammar_symbol, current_node_in_tree = stack.pop() # Desempaquetar
        
        current_token_object = tokens_for_parsing[index]
        current_token_type_from_lexer = current_token_object.type # Este es el que compararemos

        stack_str = ' '.join([s[0] for s in stack + [(top_grammar_symbol, current_node_in_tree)]]) # Mostrar solo el símbolo de la gramática
        
        # Mostrar más información del token actual
        input_token_display = f"{current_token_type_from_lexer} ({current_token_object.value}, L{current_token_object.lineno})"
        input_token_display = input_token_display[:ancho_input-3] + '...' if len(input_token_display) > ancho_input-3 else input_token_display
        
        print(f"{stack_str:<{ancho_stack}} | {input_token_display:<{ancho_input}} | ", end='')

        if top_grammar_symbol == 'epsilon': # 'epsilon' es una cadena literal que usas para producciones vacías
            print("ε (Producción vacía)")
            # Crear un nodo epsilon en el árbol si es necesario para visualización
            # current_node_in_tree.agregar_hijo(Nodo("epsilon")) # Esto es opcional, depende de cómo quieras tu árbol
            continue
        elif top_grammar_symbol == current_token_type_from_lexer: # Comparar con el TIPO de token del lexer
            print(f"Match: {current_token_type_from_lexer}")
            # El current_node_in_tree ya fue creado con top_grammar_symbol.
            # Si quieres añadir el valor del lexema al nodo:
            # current_node_in_tree.lexeme_value = current_token_object.value # Necesitarías modificar Nodo
            index += 1
        elif top_grammar_symbol in parsing_table: # top_grammar_symbol es un No-Terminal
            # Usar current_token_type_from_lexer para buscar en la tabla
            rule_body = parsing_table[top_grammar_symbol].get(current_token_type_from_lexer)
            
            if rule_body: # rule_body es una lista de símbolos de la gramática
                production_str = ' '.join(rule_body)
                print(f"{top_grammar_symbol} → {production_str}")

                # Agregar hijos al current_node_in_tree en el orden correcto
                # Los símbolos de la regla se apilan en orden inverso,
                # así que los hijos deben crearse en el orden de la regla.
                child_nodes_for_stack = []
                for grammar_symbol_in_rule in reversed(rule_body):
                    if grammar_symbol_in_rule != 'epsilon': # No crear nodos para 'epsilon' en la pila
                        # Cada símbolo en la regla (sea terminal o no-terminal) obtiene un nuevo nodo
                        child_node = Nodo(grammar_symbol_in_rule)
                        # Lo agregamos a una lista temporal para luego añadirlo al padre en el orden correcto
                        child_nodes_for_stack.append((grammar_symbol_in_rule, child_node))
                
                # Añadir los hijos al nodo padre en el orden de la regla
                for _, child_n in reversed(child_nodes_for_stack): # Invertir de nuevo para orden original
                     current_node_in_tree.agregar_hijo(child_n)
                
                # Empujar a la pila (ya están en orden inverso para la pila)
                for symbol_for_stack, node_for_stack in child_nodes_for_stack:
                    stack.append((symbol_for_stack, node_for_stack))
            else:
                print(f"\n❌ Error Sintáctico: No hay regla para ({top_grammar_symbol}, {current_token_type_from_lexer}) en la línea {current_token_object.lineno}")
                print(f"Token problemático: valor='{current_token_object.value}', tipo='{current_token_object.type}'")
                print("="*(ancho_stack + ancho_input + ancho_action + 6))
                return None
        else: # top_grammar_symbol es un Terminal, pero no coincide con current_token_type_from_lexer
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

# ... (definiciones de Nodo, imprimir_arbol, cargar_tabla_desde_csv, parser_ll1, graphviz) ...

if __name__ == '__main__':
    tabla_parsing = cargar_tabla_desde_csv("E:\\Compiladores\\Gramática\\tablitaTransiciones2.csv") # TU RUTA
    
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input4.ws" # TU RUTA

    print(f"--- Analizando léxicamente el archivo: {archivo_entrada_path} ---")
    # Llama a la función de tu analizador léxico que devuelve la lista de tokens
    # Asumo que analyze_file es la función correcta de tu AnalizadorLexico.py
    lista_de_tokens = analyze_file(archivo_entrada_path) 

    if lista_de_tokens:
        print(f"--- Tokens generados por el lexer: ---")
        for tok in lista_de_tokens:
            print(tok)
        print(f"--- Iniciando análisis sintáctico ---")
        # Pasa la lista de objetos token al parser
        arbol_sintactico = parser_ll1(lista_de_tokens, tabla_parsing, start_symbol='Program') # Asegúrate que 'Program' es tu símbolo inicial

        if arbol_sintactico:
            print("\n✅ Entrada aceptada por el analizador sintáctico.")
            
            print("\nÁrbol sintáctico en preorder (nodos de gramática):")
            arbol_sintactico.imprimir_preorden()
            
            print("\n\nEstructura del árbol sintáctico:")
            imprimir_arbol(arbol_sintactico)

            exportar_arbol_a_graphviz(arbol_sintactico, "E:\\Compiladores\\Salida Graphviz\\arbol_parseo.txt") # TU RUTA y extensión .dot
            print("\nÁrbol exportado a 'arbol_parseo.dot'. Puedes visualizarlo con Graphviz (ej: dot -Tpng arbol_parseo.dot -o arbol.png)")
        else:
            print("\n❌ Entrada rechazada por el analizador sintáctico.")
    else:
        print("\n❌ Error durante el análisis léxico o el archivo no contiene tokens.")