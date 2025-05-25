import csv
import ply.lex as lex
from AnalizadorLexico import analyze_file
class Nodo:
    def __init__(self, valor, token_original=None):  
        self.valor = valor
        self.hijos = []
        self.token_original = token_original 

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)

    def imprimir_preorden(self):
        print(self.valor, end='')
        if self.hijos:
            print(" (", end='')
            for i, hijo in enumerate(self.hijos):
                hijo.imprimir_preorden()
                if i < len(self.hijos) - 1:
                    print(", ", end='')
            print(")", end='')

def imprimir_arbol(nodo, nivel=0, prefijo='', es_ultimo=True):
    espacio = '    '
    rama = '│   '
    rama_esquina = '└── '
    rama_t = '├── '
    
    conector = rama_esquina if es_ultimo else rama_t
    
    valor_display = nodo.valor
    if nodo.valor == 'epsilon_node': 
        valor_display = "ε"
    elif isinstance(nodo.valor, str) and nodo.valor.startswith("'") and nodo.valor.endswith("'"):
        valor_display = f"{nodo.valor}"
    elif not nodo.hijos and not (isinstance(nodo.valor, str) and nodo.valor.isupper() and nodo.valor.endswith("_TOKEN")) and nodo.valor != "ε":
        if not (isinstance(nodo.valor, str) and nodo.valor.startswith("'")):
             valor_display = f"'{nodo.valor}'"

    if nivel > 0:
        print(f"{prefijo}{conector}{valor_display}")
    else:
        print(f"{espacio}{valor_display}") 

    nuevo_prefijo = prefijo + (espacio if es_ultimo else rama)
    
    num_hijos = len(nodo.hijos)
    for i, hijo in enumerate(nodo.hijos):
        imprimir_arbol(hijo, nivel + 1, nuevo_prefijo, i == num_hijos - 1)

def cargar_tabla_desde_csv(nombre_archivo):
    tabla = {}
    try:
        with open(nombre_archivo, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            encabezado_completo = next(reader)
            if not encabezado_completo:
                print(f"Error: El archivo CSV '{nombre_archivo}' tiene una cabecera vacía.")
                return None
            encabezado = encabezado_completo[1:]

            for fila in reader:
                if not fila: continue
                no_terminal = fila[0].strip()
                if not no_terminal: continue

                tabla[no_terminal] = {}
                for i, terminal_header in enumerate(encabezado):
                    if i + 1 < len(fila):
                        celda = fila[i+1].strip()
                        if celda:
                            if celda.lower() == 'epsilon':
                                tabla[no_terminal][terminal_header.strip()] = ['epsilon_rule'] 
                            else:
                                tabla[no_terminal][terminal_header.strip()] = celda.split()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo CSV '{nombre_archivo}'.")
        return None
    except Exception as e:
        print(f"Error al cargar la tabla desde CSV '{nombre_archivo}': {e}")
        return None
    return tabla

TOKENS_CON_LEXEMA = {
    'IDENTIFICADOR_TOKEN',
    'QILLQA_TOKEN',
    'YUPAY_TOKEN',
    'CHIQI_KAY_TOKEN',
}

def parser_ll1(token_objects_list, parsing_table, start_symbol='Program'): 
    if not token_objects_list:
        print("Error: La lista de tokens está vacía.")
        return None
    if not parsing_table:
        print("Error: La tabla de parsing no se cargó correctamente.")
        return None

    eof_token = lex.LexToken()
    eof_token.type = '$'
    eof_token.value = '$'
    eof_token.lineno = token_objects_list[-1].lineno if token_objects_list else 0
    eof_token.lexpos = token_objects_list[-1].lexpos if token_objects_list else 0
    
    tokens_for_parsing = token_objects_list + [eof_token]
    index = 0

    raiz = Nodo(start_symbol) 
    stack = [('$', None), (start_symbol, raiz)]

    ancho_stack = 50
    ancho_input = 65
    ancho_action = 50

    print("\n" + "="*(ancho_stack + ancho_input + ancho_action + 6))
    print(f"{'Stack':<{ancho_stack}} | {'Input Token (Type, Value, Line)':<{ancho_input}} | {'Action':<{ancho_action}}")
    print("-"*(ancho_stack + ancho_input + ancho_action + 6))

    while stack:
        if index >= len(tokens_for_parsing):
            print("\n❌ Error Sintáctico: Se alcanzó el final de los tokens inesperadamente pero la pila no está vacía.")
            print(f"Pila restante: {[s[0] for s in stack]}")
            print("="*(ancho_stack + ancho_input + ancho_action + 6))
            return None

        top_grammar_symbol, current_node_in_tree = stack[-1]
        stack.pop()
        
        current_token_object = tokens_for_parsing[index]
        current_token_type_from_lexer = current_token_object.type

        stack_display_list = [s[0] for s in reversed(stack + [(top_grammar_symbol, current_node_in_tree)])]
        stack_str_print = ' '.join(stack_display_list)
        
        input_token_display = f"{current_token_type_from_lexer} ('{current_token_object.value}', L{current_token_object.lineno})"
        input_token_display = input_token_display[:ancho_input-3] + '...' if len(input_token_display) > ancho_input-3 else input_token_display
        
        print(f"{stack_str_print:<{ancho_stack}} | {input_token_display:<{ancho_input}} | ", end='')

        if top_grammar_symbol == 'epsilon_node': 
            print("ε (Nodo Epsilon en Árbol)")
            
            continue
        elif top_grammar_symbol == current_token_type_from_lexer: 
            print(f"Match: {current_token_type_from_lexer}")
            if current_node_in_tree: 
                current_node_in_tree.token_original = current_token_object

            if top_grammar_symbol in TOKENS_CON_LEXEMA:
                lexeme_node = Nodo(str(current_token_object.value), current_token_object) 
                if current_node_in_tree:
                    current_node_in_tree.agregar_hijo(lexeme_node)
            index += 1
        elif top_grammar_symbol in parsing_table:
            if current_token_type_from_lexer not in parsing_table[top_grammar_symbol]:
                print(f"\n❌ Error Sintáctico: No hay regla para ({top_grammar_symbol}, {current_token_type_from_lexer}) en la línea {current_token_object.lineno}")
                print(f"Token problemático: valor='{current_token_object.value}', tipo='{current_token_object.type}'")
                print(f"Posibles tokens para '{top_grammar_symbol}': {list(parsing_table[top_grammar_symbol].keys())}")
                print("="*(ancho_stack + ancho_input + ancho_action + 6))
                return None

            rule_body = parsing_table[top_grammar_symbol].get(current_token_type_from_lexer)
            
            if rule_body:
                production_str = ' '.join(rule_body if rule_body != ['epsilon_rule'] else ['ε'])
                print(f"{top_grammar_symbol} → {production_str}")

                nodes_for_stack_addition = []
                
                if rule_body == ['epsilon_rule']: 
                    epsilon_tree_node = Nodo('epsilon_node')
                    nodes_for_stack_addition.append(('epsilon_node', epsilon_tree_node))
                else:
                    for grammar_symbol_in_rule in reversed(rule_body):
                        child_node = Nodo(grammar_symbol_in_rule)
                        nodes_for_stack_addition.append((grammar_symbol_in_rule, child_node))
                
                for grammar_symbol_for_child, child_n in reversed(nodes_for_stack_addition):
                     if current_node_in_tree:
                        current_node_in_tree.agregar_hijo(child_n)
                
                for symbol_for_stack, node_for_stack in nodes_for_stack_addition:
                    stack.append((symbol_for_stack, node_for_stack))
        else:
            print(f"\n❌ Error Sintáctico: Se esperaba '{top_grammar_symbol}' pero se encontró '{current_token_type_from_lexer}' (valor: '{current_token_object.value}') en la línea {current_token_object.lineno}")
            print("="*(ancho_stack + ancho_input + ancho_action + 6))
            return None

        if len(stack) == 1 and stack[0][0] == '$' and current_token_type_from_lexer == '$':
            if top_grammar_symbol != '$':
                final_stack_str = '$'
                final_input_display = f"$ ('{current_token_object.value}', L{current_token_object.lineno})"
                pass 

            if top_grammar_symbol == '$': 
                print("="*(ancho_stack + ancho_input + ancho_action + 6))
                print(f"{'$':<{ancho_stack}} | {'$':<{ancho_input}} | ACEPTADO") 
                print("="*(ancho_stack + ancho_input + ancho_action + 6))
                return raiz
        elif not stack and current_token_type_from_lexer != '$':
            print(f"\n❌ Error Sintáctico: Pila vacía pero aún quedan tokens de entrada. Token actual: {current_token_type_from_lexer}")
            print("="*(ancho_stack + ancho_input + ancho_action + 6))
            return None

    if index < len(tokens_for_parsing) -1 :
        print(f"\n❌ Error Sintáctico: Entrada no consumida completamente. Próximo token: {tokens_for_parsing[index].type}")
    elif stack:
         print(f"\n❌ Error Sintáctico: Pila no vacía al final de la entrada. Pila: {[s[0] for s in stack]}")
    else: 
        if current_token_type_from_lexer == '$':
             print("="*(ancho_stack + ancho_input + ancho_action + 6))
             print(f"{'$':<{ancho_stack}} | {'$':<{ancho_input}} | ACEPTADO (Condición final)")
             print("="*(ancho_stack + ancho_input + ancho_action + 6))
             return raiz

    print("="*(ancho_stack + ancho_input + ancho_action + 6))
    return None


def generar_graphviz(nodo, archivo, contador=[0], conexiones=None):
    if conexiones is None:
        conexiones = []
    
    id_actual = contador[0]
    label_valor = str(nodo.valor).replace('"', '\\"')
    if nodo.valor == 'epsilon_node':
        label_valor = "ε"
    archivo.write(f'  node{id_actual} [label="{label_valor}"];\n')
    nodo_id = id_actual
    contador[0] += 1
    
    for hijo in nodo.hijos:
        hijo_id = generar_graphviz(hijo, archivo, contador, conexiones)
        conexiones.append((nodo_id, hijo_id))
    return nodo_id


def exportar_arbol_a_graphviz(raiz, nombre_archivo="arbol_parseo.dot"):
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write("digraph G {\n")
        archivo.write('  node [fontname="Arial"];\n')
        conexiones = []
        generar_graphviz(raiz, archivo, [0], conexiones)
        
        for origen, destino in conexiones:
            archivo.write(f"  node{origen} -> node{destino};\n")
        archivo.write("}\n")
    print(f"Árbol exportado a '{nombre_archivo}'. Puedes visualizarlo con Graphviz (ej: dot -Tpng {nombre_archivo} -o arbol.png)")


if __name__ == '__main__':
    tabla_csv_path = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv"
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input3.ws"

    print(f"--- Cargando tabla de parsing desde: {tabla_csv_path} ---")
    tabla_parsing = cargar_tabla_desde_csv(tabla_csv_path)
    
    if tabla_parsing is None:
        print("No se pudo continuar debido a un error al cargar la tabla de parsing.")
    else:
        print(f"--- Analizando léxicamente el archivo: {archivo_entrada_path} ---")
        lista_de_tokens = analyze_file(archivo_entrada_path) 

        if lista_de_tokens:
            print(f"--- Iniciando análisis sintáctico ---")
            arbol_sintactico = parser_ll1(lista_de_tokens, tabla_parsing, start_symbol='Program')

            if arbol_sintactico:
                print("\n✅ Entrada aceptada por el analizador sintáctico.")
                
                print("\n\nEstructura del árbol sintáctico:")
                imprimir_arbol(arbol_sintactico)

                exportar_arbol_a_graphviz(arbol_sintactico, "E:\\Compiladores\\Salida Graphviz\\arbol_parseo.txt")
            else:
                print("\n❌ Entrada rechazada por el analizador sintáctico.")
        else:
            print("\n❌ Error durante el análisis léxico o el archivo no contiene tokens.")