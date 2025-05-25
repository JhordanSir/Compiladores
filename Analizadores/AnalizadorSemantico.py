# --- START OF FILE analizadorSintactico.py ---
import csv
import ply.lex as lex
from AnalizadorLexico import analyze_file # Make sure AnalizadorLexico.py is accessible
from prettytable import PrettyTable

class Nodo:
    def __init__(self, valor):
        self.valor = valor
        self.hijos = []

    def agregar_hijo(self, hijo):
        self.hijos.append(hijo)

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
    elif not nodo.hijos and not (isinstance(nodo.valor, str) and (nodo.valor.isupper() and nodo.valor.endswith("_TOKEN")) or nodo.valor == "ε" or (nodo.valor.startswith("'") and nodo.valor.endswith("'")) ):
        valor_display = f"'{nodo.valor}'"

    if nivel > 0:
        print(f"{prefijo}{conector}{valor_display}")
    else:
        print(f"{valor_display}")

    nuevo_prefijo = prefijo + (espacio if es_ultimo else rama)
    
    num_hijos = len(nodo.hijos)
    for i, hijo in enumerate(nodo.hijos):
        imprimir_arbol(hijo, nivel + 1, nuevo_prefijo, i == num_hijos - 1)

class SymbolTable:
    def __init__(self):
        self.scopes = [{'name': 'global', 'symbols': {}, 'parent_index': None}]
        self.current_scope_index = 0
        print("SymbolTable initialized. Current scope: global")

    def enter_scope(self, name):
        parent_index = self.current_scope_index
        new_scope = {'name': name, 'symbols': {}, 'parent_index': parent_index}
        self.scopes.append(new_scope)
        self.current_scope_index = len(self.scopes) - 1
        print(f"DEBUG SymbolTable: Entered scope: {name}. Parent: {self.scopes[parent_index]['name'] if parent_index is not None else 'None'}. Current index: {self.current_scope_index}")

    def exit_scope(self):
        if self.scopes[self.current_scope_index]['parent_index'] is not None:
            exiting_scope_name = self.scopes[self.current_scope_index]['name']
            self.current_scope_index = self.scopes[self.current_scope_index]['parent_index']
            print(f"DEBUG SymbolTable: Exited scope: {exiting_scope_name}. Current scope: {self.scopes[self.current_scope_index]['name']}. Current index: {self.current_scope_index}")
        else:
            print("DEBUG SymbolTable: Warning: Attempted to exit global scope or already at global.")

    def add_symbol(self, name, kind, data_type, line=None):
        current_scope_dict = self.scopes[self.current_scope_index]
        if name in current_scope_dict['symbols']:
            print(f"Error Semántico: El símbolo '{name}' ya está declarado en el ámbito '{current_scope_dict['name']}'. Línea: {line if line else 'N/A'}")
            return False
        current_scope_dict['symbols'][name] = {'kind': kind, 'type': data_type, 'line': line}
        print(f"DEBUG SymbolTable: Added symbol: {name} (Kind: {kind}, Type: {data_type}, Line: {line if line else 'N/A'}) to scope: {current_scope_dict['name']}")
        return True

    def display(self):
        print("\n--- Tabla de Símbolos ---")
        for i, scope in enumerate(self.scopes):
            parent_name = "Ninguno"
            if scope['parent_index'] is not None and scope['parent_index'] < len(self.scopes) :
                 parent_name = self.scopes[scope['parent_index']]['name']

            print(f"\nÁmbito #{i}: {scope['name']} (Padre: {parent_name})")
            if not scope['symbols']:
                print("  (Vacío)")
                continue
            table = PrettyTable(["Nombre", "Tipo (Kind)", "Tipo de Dato", "Línea"])
            for name, details in scope['symbols'].items():
                table.add_row([name, details['kind'], details['type'], details.get('line', 'N/A')])
            print(table)
        print("------------------------")

# --- Helper functions for Simplified Pre-order Traversal ---
def get_direct_child_value(parent_node, child_node_name_to_find):
    """Finds a direct child node by its 'valor' and returns the child node itself."""
    if parent_node and hasattr(parent_node, 'hijos'):
        for child in parent_node.hijos:
            if hasattr(child, 'valor') and child.valor == child_node_name_to_find:
                return child 
    return None

def get_identifier_string_from_id_node(id_node):
    """Given an IDENTIFICADOR_TOKEN node, returns its child's value (the actual string)."""
    if id_node and hasattr(id_node, 'valor') and id_node.valor == 'IDENTIFICADOR_TOKEN' and \
       hasattr(id_node, 'hijos') and id_node.hijos:
        if hasattr(id_node.hijos[0], 'valor'):
            return id_node.hijos[0].valor
    return None

def find_type_in_declaration_children(declaration_node):
    """
    Searches children of a declaration node (VarDeclaration, Parameter, FunctionDeclaration for return type)
    for a TIPO_xxx token or a 'Type' non-terminal whose child is a TIPO_xxx token.
    """
    if declaration_node and hasattr(declaration_node, 'hijos'):
        for child in declaration_node.hijos:
            if hasattr(child, 'valor'):
                if isinstance(child.valor, str) and child.valor.startswith('TIPO_'):
                    # print(f"DEBUG find_type: Found direct TIPO_ token: {child.valor} in {declaration_node.valor}")
                    return child.valor 
                elif child.valor == 'Type': 
                    # print(f"DEBUG find_type: Found 'Type' NT in {declaration_node.valor}")
                    if hasattr(child, 'hijos') and child.hijos and \
                       hasattr(child.hijos[0], 'valor') and \
                       isinstance(child.hijos[0].valor, str) and \
                       child.hijos[0].valor.startswith('TIPO_'):
                        # print(f"DEBUG find_type: Found type {child.hijos[0].valor} under 'Type' NT.")
                        return child.hijos[0].valor
    # print(f"DEBUG find_type: No type found in children of {declaration_node.valor if hasattr(declaration_node, 'valor') else 'Unknown Node'}")
    return None


# --- Simplified Semantic Analysis and Symbol Table Construction (Pre-order) ---
def construir_tabla_simbolos_preorden(nodo, symbol_table):
    # print(f"\nDEBUG CSTP: Called with node: {nodo}") 
    if nodo is None:
        # print("DEBUG CSTP: Node is None. Returning.")
        return
    if not hasattr(nodo, 'valor'):
        # print(f"DEBUG CSTP: Node {nodo} has no 'valor' attribute. Returning.")
        return

    node_name = nodo.valor
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # !! CRITICAL DEBUG PRINT: ENSURE THIS IS ACTIVE !!
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    print(f"PRE-ORDER VISIT: Node Value = '{node_name}'")
    # if hasattr(nodo, 'hijos') and nodo.hijos:
    #     print(f"  Children of '{node_name}': {[h.valor for h in nodo.hijos if hasattr(h, 'valor')]}")
    # else:
    #     print(f"  Node '{node_name}' has no children or children have no 'valor'")
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    # --- Actions at the current node (PRE-ORDER) ---
    # >>>>>>>>> MAKE SURE THESE STRING LITERALS MATCH YOUR PARSE TREE NODE VALUES <<<<<<<<<<<<
    if node_name == 'FunctionDeclaration': # e.g., if your tree uses "FuncDecl" then this will fail
        print(f"DEBUG CSTP: Matched 'FunctionDeclaration': {node_name}")
        id_node = get_direct_child_value(nodo, 'IDENTIFICADOR_TOKEN')
        func_name = get_identifier_string_from_id_node(id_node)
        
        print(f"DEBUG CSTP: FunctionDeclaration - Extracted func_name: '{func_name}'")

        if func_name:
            original_scope_index = symbol_table.current_scope_index
            is_global_scope = (symbol_table.scopes[symbol_table.current_scope_index]['name'] == 'global')
            if not is_global_scope:
                # print("DEBUG CSTP: FunctionDeclaration - Not in global, navigating to global.")
                while symbol_table.scopes[symbol_table.current_scope_index]['parent_index'] is not None:
                    symbol_table.exit_scope()

            # Determine return type
            return_type = "void" 
            parentesis_cierra_node = get_direct_child_value(nodo, 'PARENTESIS_CIERRA')
            block_node = get_direct_child_value(nodo, 'Block') # Assuming Block is your NT for function body
            if parentesis_cierra_node and hasattr(nodo, 'hijos'):
                try:
                    idx_paren_cierra = nodo.hijos.index(parentesis_cierra_node)
                    idx_block = len(nodo.hijos) 
                    if block_node: # If there's an explicit Block node
                         idx_block = nodo.hijos.index(block_node)
                    
                    # Look for Type or TIPO_ token between ')' and '{' (or Block)
                    for i in range(idx_paren_cierra + 1, idx_block):
                        potential_type_node = nodo.hijos[i]
                        found_rt = None
                        if hasattr(potential_type_node, 'valor'):
                            if potential_type_node.valor.startswith('TIPO_'):
                                found_rt = potential_type_node.valor
                            elif potential_type_node.valor == 'Type': # Non-terminal 'Type'
                                found_rt = find_type_in_declaration_children(potential_type_node)
                        
                        if found_rt:
                            return_type = found_rt
                            # print(f"DEBUG CSTP: FunctionDeclaration - Deduced return type: '{return_type}' for '{func_name}'")
                            break
                except ValueError: 
                    # print(f"DEBUG CSTP: FunctionDeclaration - ValueError finding parens/block for return type of '{func_name}'")
                    pass


            # print(f"DEBUG CSTP: FunctionDeclaration - Adding function '{func_name}' (type: {return_type}) to global scope.")
            symbol_table.add_symbol(func_name, 'function', return_type) 

            if not is_global_scope: # Restore original scope before entering function's own
                 symbol_table.current_scope_index = original_scope_index
            
            # print(f"DEBUG CSTP: FunctionDeclaration - Entering scope for function '{func_name}'.")
            symbol_table.enter_scope(f"function_{func_name}")

            # Process parameters
            parameters_node = get_direct_child_value(nodo, 'Parameters') # Your NT for parameter list
            if parameters_node and hasattr(parameters_node, 'hijos'):
                # print(f"DEBUG CSTP: FunctionDeclaration - Processing parameters for '{func_name}'.")
                q_params = [parameters_node]
                visited_params_containers = set()
                while q_params:
                    param_container = q_params.pop(0)
                    if not param_container or id(param_container) in visited_params_containers: continue
                    visited_params_containers.add(id(param_container))

                    if hasattr(param_container, 'hijos'):
                        for child_param_node in param_container.hijos:
                            if hasattr(child_param_node, 'valor'):
                                if child_param_node.valor == 'Parameter': # Your NT for a single parameter
                                    # print(f"DEBUG CSTP: FunctionDeclaration - Found 'Parameter' NT child.")
                                    param_id_node = get_direct_child_value(child_param_node, 'IDENTIFICADOR_TOKEN')
                                    param_name_str = get_identifier_string_from_id_node(param_id_node)
                                    param_type_str = find_type_in_declaration_children(child_param_node) # Search in 'Parameter's children
                                    # print(f"DEBUG CSTP: FunctionDeclaration - Extracted param: Name='{param_name_str}', Type='{param_type_str}'")
                                    if param_name_str and param_type_str:
                                        symbol_table.add_symbol(param_name_str, 'parameter', param_type_str)
                                # For recursive parameter list structures like Parameters_prime -> COMA Parameter Parameters_prime
                                elif child_param_node.valor in ['Parameters_prime', 'MoreParameters', 'ParameterList', 'ParamPrime', 'ParamsRest']: # Adjust to your grammar's list NTs
                                    q_params.append(child_param_node)
            # else:
                # print(f"DEBUG CSTP: FunctionDeclaration - No 'Parameters' node or it's empty for '{func_name}'.")
        else:
            print(f"DEBUG CSTP: FunctionDeclaration node found, but func_name could not be extracted.")


    elif node_name == 'VarDeclaration': # e.g., if your tree uses "VariableDeclaration" this will fail
        print(f"DEBUG CSTP: Matched 'VarDeclaration': {node_name}")
        id_node = get_direct_child_value(nodo, 'IDENTIFICADOR_TOKEN')
        var_name = get_identifier_string_from_id_node(id_node)
        var_type = find_type_in_declaration_children(nodo) 
        
        # print(f"DEBUG CSTP: VarDeclaration - Extracted var_name: '{var_name}', var_type: '{var_type}'")
        if var_name and var_type:
            symbol_table.add_symbol(var_name, 'variable', var_type)
        else:
            print(f"DEBUG CSTP: VarDeclaration - Failed to add. Name: '{var_name}', Type: '{var_type}'")
            # if id_node: print(f"  VarDecl id_node value: {id_node.valor}")
            # else: print("  VarDecl id_node is None")
            # print(f"  Children of VarDeclaration: {[c.valor for c in nodo.hijos if hasattr(c, 'valor')] if hasattr(nodo, 'hijos') else 'No children'}")


    elif node_name == 'ConstDeclaration': # If you have constants
        print(f"DEBUG CSTP: Matched 'ConstDeclaration': {node_name}")
        id_node = get_direct_child_value(nodo, 'IDENTIFICADOR_TOKEN')
        const_name = get_identifier_string_from_id_node(id_node)
        const_type = find_type_in_declaration_children(nodo)
        
        # print(f"DEBUG CSTP: ConstDeclaration - Extracted const_name: '{const_name}', const_type: '{const_type}'")
        if const_name and const_type:
            symbol_table.add_symbol(const_name, 'constant', const_type)


    # --- Recursively visit children ---
    if hasattr(nodo, 'hijos'):
        # print(f"DEBUG CSTP: Node '{node_name}' - Recursing into children...")
        for i, hijo in enumerate(nodo.hijos):
            # print(f"DEBUG CSTP: Node '{node_name}' - Recursing into child #{i} (Value: '{hijo.valor if hasattr(hijo, 'valor') else 'NoValor'}')")
            if node_name == 'IDENTIFICADOR_TOKEN' and not hasattr(hijo, 'hijos'): # Don't recurse into the string leaf of ID_TOKEN
                # print(f"DEBUG CSTP: Node '{node_name}' - Skipping recursion into IDENTIFICADOR_TOKEN's leaf child '{hijo.valor if hasattr(hijo, 'valor') else 'NoValor'}'.")
                continue
            construir_tabla_simbolos_preorden(hijo, symbol_table)
    # else:
        # print(f"DEBUG CSTP: Node '{node_name}' has no children to recurse into.")

    # --- Actions after visiting children (POST-ORDER) ---
    if node_name == 'FunctionDeclaration':
        # func_name might not be defined if extraction failed earlier, handle gracefully for debug print
        fn_debug_name = "UnknownFunc (extraction failed)"
        # Attempt to re-extract func_name for the debug message if it wasn't in locals()
        # This isn't ideal but helps with the printout.
        if 'func_name' in locals() and func_name: # Check if func_name was successfully extracted
            fn_debug_name = func_name
        else: # Try to get it again just for this debug message
            temp_id_node = get_direct_child_value(nodo, 'IDENTIFICADOR_TOKEN')
            temp_fn_name = get_identifier_string_from_id_node(temp_id_node)
            if temp_fn_name:
                fn_debug_name = temp_fn_name
        
        print(f"DEBUG CSTP: Post-order exiting scope for 'FunctionDeclaration' (likely '{fn_debug_name}').")
        symbol_table.exit_scope()


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
    ancho_action = 60 

    print("\n" + "="*(ancho_stack + ancho_input + ancho_action + 8)) 
    print(f"{'Stack':<{ancho_stack}} | {'Input Token (Type, Value, Line)':<{ancho_input}} | {'Action':<{ancho_action}}")
    print("-"*(ancho_stack + ancho_input + ancho_action + 8))

    while stack:
        if index >= len(tokens_for_parsing):
            print("\n❌ Error Sintáctico: Se alcanzó el final de los tokens inesperadamente pero la pila no está vacía.")
            print(f"Pila restante: {[s[0] for s in stack]}")
            print("="*(ancho_stack + ancho_input + ancho_action + 8))
            return None

        top_grammar_symbol, current_node_in_tree = stack.pop() 
        
        current_token_object = tokens_for_parsing[index]
        current_token_type_from_lexer = current_token_object.type

        stack_display_list = [top_grammar_symbol] + [s[0] for s in reversed(stack)]
        stack_str_print = ' '.join(stack_display_list)
        
        input_token_display = f"{current_token_type_from_lexer} ('{current_token_object.value}', L{current_token_object.lineno})"
        input_token_display_truncated = (input_token_display[:ancho_input-3] + '...') if len(input_token_display) > ancho_input else input_token_display
        
        print(f"{stack_str_print:<{ancho_stack}} | {input_token_display_truncated:<{ancho_input}} | ", end='')

        if top_grammar_symbol == 'epsilon_node': 
            print("ε (Nodo Epsilon en Árbol)")
            continue
        elif top_grammar_symbol == current_token_type_from_lexer:
            print(f"Match: {current_token_type_from_lexer}")
            
            if top_grammar_symbol in TOKENS_CON_LEXEMA:
                lexeme_node = Nodo(str(current_token_object.value)) 
                if current_node_in_tree: 
                     current_node_in_tree.agregar_hijo(lexeme_node)
            index += 1
        elif top_grammar_symbol in parsing_table: 
            if current_token_type_from_lexer not in parsing_table[top_grammar_symbol]:
                print(f"\n❌ Error Sintáctico: No hay regla para ({top_grammar_symbol}, {current_token_type_from_lexer}) en la línea {current_token_object.lineno}")
                print(f"Token problemático: valor='{current_token_object.value}', tipo='{current_token_object.type}'")
                print(f"Posibles tokens para '{top_grammar_symbol}': {list(parsing_table[top_grammar_symbol].keys())}")
                print("="*(ancho_stack + ancho_input + ancho_action + 8))
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
                    child_nodes_for_tree = [Nodo(grammar_symbol_in_rule) for grammar_symbol_in_rule in rule_body]
                    
                    for i in range(len(rule_body) - 1, -1, -1):
                        grammar_symbol_in_rule = rule_body[i]
                        node_for_this_symbol = child_nodes_for_tree[i]
                        nodes_for_stack_addition.append((grammar_symbol_in_rule, node_for_this_symbol))
                
                if current_node_in_tree: 
                    if rule_body == ['epsilon_rule']:
                        current_node_in_tree.agregar_hijo(nodes_for_stack_addition[0][1]) 
                    else:
                        for grammar_symbol_for_child, child_n in reversed(nodes_for_stack_addition): 
                             current_node_in_tree.agregar_hijo(child_n)
                
                for symbol_for_stack, node_for_stack in nodes_for_stack_addition:
                    stack.append((symbol_for_stack, node_for_stack))
        else: 
            print(f"\n❌ Error Sintáctico: Se esperaba '{top_grammar_symbol}' pero se encontró '{current_token_type_from_lexer}' (valor: '{current_token_object.value}') en la línea {current_token_object.lineno}")
            print("="*(ancho_stack + ancho_input + ancho_action + 8))
            return None

        if not stack: 
            if current_token_type_from_lexer == '$': 
                 print(f"{'':<{ancho_stack}} | {'$':<{ancho_input}} | ACEPTADO (Pila vacía, fin de entrada)")
                 print("="*(ancho_stack + ancho_input + ancho_action + 8))
                 return raiz
            else: 
                print(f"\n❌ Error Sintáctico: Pila vacía pero aún quedan tokens de entrada. Token actual: {current_token_type_from_lexer}")
                print("="*(ancho_stack + ancho_input + ancho_action + 8))
                return None
        
        if len(stack) == 1 and stack[0][0] == '$' and current_token_type_from_lexer == '$':
            if top_grammar_symbol == '$':
                 print(f"{'$':<{ancho_stack}} | {'$':<{ancho_input}} | ACEPTADO") 
                 print("="*(ancho_stack + ancho_input + ancho_action + 8))
                 return raiz

    if index < len(tokens_for_parsing) -1 : 
        print(f"\n❌ Error Sintáctico: Entrada no consumida completamente. Próximo token: {tokens_for_parsing[index].type}")
    elif stack and not (len(stack) == 1 and stack[0][0] == '$'): 
         print(f"\n❌ Error Sintáctico: Pila no vacía al final de la entrada. Pila: {[s[0] for s in stack]}")

    print("="*(ancho_stack + ancho_input + ancho_action + 8))
    return None 


def generar_graphviz(nodo, archivo, contador=[0], conexiones=None, parent_id=None):
    if conexiones is None:
        conexiones = [] 
    
    current_id = contador[0]
    label_valor = str(nodo.valor).replace('"', '\\"')
    if nodo.valor == 'epsilon_node':
        label_valor = "ε"
    elif not nodo.hijos and not (isinstance(nodo.valor, str) and (nodo.valor.isupper() and nodo.valor.endswith("_TOKEN")) or nodo.valor == "ε" or (nodo.valor.startswith("'") and nodo.valor.endswith("'")) ):
         label_valor = f"'{label_valor}'"

    archivo.write(f'  node{current_id} [label="{label_valor}"];\n')
    
    if parent_id is not None:
        conexiones.append((parent_id, current_id))
    
    contador[0] += 1
    
    for hijo in nodo.hijos:
        generar_graphviz(hijo, archivo, contador, conexiones, current_id)
    
    if parent_id is None:
        return conexiones
    return None 

def exportar_arbol_a_graphviz(raiz, nombre_archivo="arbol_parseo.dot"):
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write("digraph G {\n")
        archivo.write('  graph [ordering="out"];\n') 
        archivo.write('  node [fontname="Arial"];\n')
        
        conexiones = generar_graphviz(raiz, archivo) 
        
        if conexiones: 
            for origen, destino in conexiones:
                archivo.write(f"  node{origen} -> node{destino};\n")
        archivo.write("}\n")
    print(f"Árbol exportado a '{nombre_archivo}'. Puedes visualizarlo con Graphviz (ej: dot -Tpng {nombre_archivo} -o arbol.png)")


if __name__ == '__main__':
    tabla_csv_path = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv"
    # Use an input file that tests scopes:
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input1.ws" 
    

    print(f"--- Cargando tabla de parsing desde: {tabla_csv_path} ---")
    tabla_parsing = cargar_tabla_desde_csv(tabla_csv_path)
    
    if tabla_parsing is None:
        print("No se pudo continuar debido a un error al cargar la tabla de parsing.")
    else:
        print(f"--- Analizando léxicamente el archivo: {archivo_entrada_path} ---")
        lista_de_tokens = analyze_file(archivo_entrada_path) 

        if lista_de_tokens:
            print(f"\n--- Iniciando análisis sintáctico ---")
            # Define your grammar's start symbol here, e.g., 'Program', 'Start', etc.
            # It must match the non-terminal used as the starting point in your LL(1) table.
            arbol_sintactico = parser_ll1(lista_de_tokens, tabla_parsing, start_symbol='Program') # Ensure 'Program' is your actual start symbol

            if arbol_sintactico:
                print("\n✅ Entrada aceptada por el analizador sintáctico.")
                print(f"DEBUG: arbol_sintactico object: {arbol_sintactico}")
                print(f"DEBUG: type(arbol_sintactico): {type(arbol_sintactico)}")
                if hasattr(arbol_sintactico, 'valor'):
                    print(f"DEBUG: arbol_sintactico.valor: {arbol_sintactico.valor}")
                if hasattr(arbol_sintactico, 'hijos'):
                    print(f"DEBUG: arbol_sintactico has {len(arbol_sintactico.hijos)} children.")
                
                print("\n\nEstructura del árbol sintáctico:")
                imprimir_arbol(arbol_sintactico)

                graphviz_output_path = "E:\\Compiladores\\Salida Graphviz\\arbol_parseo.dot"
                exportar_arbol_a_graphviz(arbol_sintactico, graphviz_output_path)
                
                print("\n--- Iniciando análisis semántico y construcción de tabla de símbolos (Pre-orden) ---")
                tabla_de_simbolos = SymbolTable()
                # USE THE PRE-ORDER FUNCTION HERE
                construir_tabla_simbolos_preorden(arbol_sintactico, tabla_de_simbolos)
                tabla_de_simbolos.display()

            else:
                print("\n❌ Entrada rechazada por el analizador sintáctico (arbol_sintactico is None).")
        else:
            print("\n❌ Error durante el análisis léxico o el archivo no contiene tokens.")
# --- END OF FILE analizadorSintactico.py ---