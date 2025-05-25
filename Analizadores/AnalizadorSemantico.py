from AnalizadorLexico import analyze_file
from analizadorSintactico import * 
import tempfile
import os

class Symbol:
    def __init__(self, name, data_type, scope_name, line_declared, symbol_type="variable"):
        self.name = name
        self.data_type = data_type
        self.scope_name = scope_name
        self.line_declared = line_declared
        self.symbol_type = symbol_type

    def __str__(self):
        return f"Symbol(Nombre: {self.name}, TipoDato: {self.data_type}, Ambito: {self.scope_name}, TipoSimbolo: {self.symbol_type}, Linea: {self.line_declared})"

class ScopeManager:
    def __init__(self):
        self.symbol_table = []
        self.scope_stack = []
        self.current_scope_name = None

    def enter_scope(self, name):
        self.scope_stack.append(name)
        self.current_scope_name = name

    def exit_scope(self):
        if self.scope_stack:
            exited_scope = self.scope_stack.pop()
            self.current_scope_name = self.scope_stack[-1] if self.scope_stack else None
        else:
            self.current_scope_name = None

    def add_symbol(self, symbol_name, data_type, line_declared, symbol_type="variable"):
        if not self.current_scope_name:
            print("Error Semántico: Intento de declarar símbolo fuera de cualquier ámbito.")
            return False
        for sym in self.symbol_table:
            if sym.name == symbol_name and sym.scope_name == self.current_scope_name:
                print(f"Error Semántico (Línea {line_declared}): Símbolo '{symbol_name}' ya declarado en el ámbito '{self.current_scope_name}'.")
                return False
        new_symbol = Symbol(symbol_name, data_type, self.current_scope_name, line_declared, symbol_type)
        self.symbol_table.append(new_symbol)
        return True

    def get_formatted_symbol_table(self):
        if not self.symbol_table:
            return "Tabla de Símbolos vacía."
        header = f"{'Nombre':<20} | {'Tipo de Dato':<15} | {'Ámbito':<20} | {'Tipo Símbolo':<15} | {'Línea Decl.':<10}"
        separator = "-" * (len(header) + 5)
        table_str = [header, separator]
        for sym in self.symbol_table:
            ambito_display = "global" if sym.scope_name == "global" else f"local ({sym.scope_name})"
            table_str.append(
                f"{sym.name:<20} | {sym.data_type:<15} | {ambito_display:<20} | {sym.symbol_type:<15} | {str(sym.line_declared):<10}"
            )
        return "\n".join(table_str)

def analizar_semantica_y_construir_tabla_simbolos(nodo_raiz, scope_manager):
    if nodo_raiz is None:
        return

    def get_node_value(node):
        if node is None: return "ERROR_NODO_NULO"
        if node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
            return node.hijos[0].valor
        return node.valor

    def get_node_line(node):
        
        if node and hasattr(node, 'token_original') and node.token_original:
            return node.token_original.lineno
        
        if node and node.valor == 'IDENTIFICADOR_TOKEN' and node.hijos and node.hijos[0] and \
           hasattr(node.hijos[0], 'token_original') and node.hijos[0].token_original:
            return node.hijos[0].token_original.lineno
        return "N/A"

    def extract_data_type_from_type_node(type_node_container):
        if type_node_container and type_node_container.valor == 'Type' and \
           type_node_container.hijos and type_node_container.hijos[0]:
            specific_type_node = type_node_container.hijos[0]
            raw_data_type = specific_type_node.valor
            if raw_data_type == 'TIPO_YUPAY': return 'yupay'
            if raw_data_type == 'TIPO_QILLQA': return 'qillqa'
            if raw_data_type == 'TIPO_CHIQI': return 'chiqi' 
            if raw_data_type == 'TIPO_CHIQAP': return 'chiqap'
            return raw_data_type
        return "desconocido"

    def visit(node):
        if node is None or node.valor == 'epsilon_node':
            return

        node_type = node.valor

        if node_type == 'Program':
            scope_manager.enter_scope("global")
            if node.hijos and node.hijos[0].valor == 'DefinitionList':
                visit(node.hijos[0])
            else:
                
                for hijo in node.hijos:
                    visit(hijo)
            scope_manager.exit_scope()

        elif node_type == 'DefinitionList':
            if not node.hijos or \
               (len(node.hijos) == 1 and node.hijos[0].valor == 'epsilon_node'):
                return

            first_child_node = node.hijos[0]

            if first_child_node.valor == 'PALABRA_RESERVADA_RURAY':
                if len(node.hijos) == 3:
                    one_definition_node = node.hijos[1]
                    remaining_definition_list_node = node.hijos[2]

                    if one_definition_node.valor == 'OneDefinition':
                        visit(one_definition_node)
                    else:
                        print(f"Error Crítico AST: Se esperaba 'OneDefinition' como segundo hijo de DefinitionList (caso RURAY), se obtuvo '{one_definition_node.valor}'")

                    if remaining_definition_list_node.valor == 'DefinitionList':
                        visit(remaining_definition_list_node)
                    else:
                        print(f"Error Crítico AST: Se esperaba 'DefinitionList' como tercer hijo de DefinitionList (caso RURAY), se obtuvo '{remaining_definition_list_node.valor}'")
                else:
                    print(f"Error Crítico AST: Estructura de DefinitionList (caso RURAY) inesperada. Número de hijos: {len(node.hijos)}. Hijos: {[h.valor for h in node.hijos]}")

            elif first_child_node.valor == 'PALABRA_RESERVADA_VAR':
                if len(node.hijos) == 6:
                    identificador_node = node.hijos[1]
                    type_container_node = node.hijos[2]
                    inicializacion_opt_node = node.hijos[3]
                    remaining_definition_list_node = node.hijos[5]

                    if scope_manager.current_scope_name != "global":
                        linea_error = get_node_line(identificador_node)
                        nombre_var_error = get_node_value(identificador_node)
                        print(f"Error Semántico (Línea {linea_error}): Variable global '{nombre_var_error}' declarada incorrectamente dentro del ámbito '{scope_manager.current_scope_name}'.")
                    
                    if identificador_node.valor == 'IDENTIFICADOR_TOKEN' and type_container_node.valor == 'Type':
                        variable_name = get_node_value(identificador_node)
                        data_type_str = extract_data_type_from_type_node(type_container_node)
                        linea_declaracion = get_node_line(identificador_node)
                        scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, symbol_type="variable")
                    else:
                        print(f"Error Crítico AST: Estructura de declaración de variable global (VAR) inesperada. ID: '{identificador_node.valor}', TypeContainer: '{type_container_node.valor}'")

                    if inicializacion_opt_node.valor == 'InicializacionOpt':
                        visit(inicializacion_opt_node)
                    else:
                        print(f"Error Crítico AST: Se esperaba 'InicializacionOpt' como cuarto hijo de DefinitionList (caso VAR), se obtuvo '{inicializacion_opt_node.valor}'")
                    
                    if remaining_definition_list_node.valor == 'DefinitionList':
                        visit(remaining_definition_list_node)
                    else:
                        print(f"Error Crítico AST: Se esperaba 'DefinitionList' como sexto hijo de DefinitionList (caso VAR), se obtuvo '{remaining_definition_list_node.valor}'")
                else:
                    print(f"Error Crítico AST: Estructura de DefinitionList (caso VAR) inesperada. Hijos: {[h.valor for h in node.hijos]}")
            else:
                print(f"Error Crítico AST: DefinitionList con primer hijo inesperado: '{first_child_node.valor}'. Hijos: {[h.valor for h in node.hijos]}")

        elif node_type == 'OneDefinition':
            nombre_funcion = "error_nombre_funcion"
            linea_decl_func = "N/A"
            tipo_retorno_str = "void"
            parametros_node = None
            type_opt_node = None
            block_node = None
            es_hatun_ruray = False

            if not node.hijos: return

            first_child_of_onedef = node.hijos[0]

            if first_child_of_onedef.valor == 'IDENTIFICADOR_TOKEN':
                nombre_funcion_node = first_child_of_onedef
                nombre_funcion = get_node_value(nombre_funcion_node)
                linea_decl_func = get_node_line(nombre_funcion_node)
                if len(node.hijos) > 2 and node.hijos[2].valor == 'ParamListOpt': parametros_node = node.hijos[2]
                if len(node.hijos) > 4 and node.hijos[4].valor == 'TypeOpt': type_opt_node = node.hijos[4]
                if len(node.hijos) > 5 and node.hijos[5].valor == 'Block': block_node = node.hijos[5]

            elif first_child_of_onedef.valor == 'HATUN_RURAY_TOKEN':
                nombre_funcion = "hatun_ruray"
                es_hatun_ruray = True
                linea_decl_func = get_node_line(first_child_of_onedef)
                if len(node.hijos) > 3 and node.hijos[3].valor == 'Block': block_node = node.hijos[3]
            else:
                for hijo in node.hijos: visit(hijo)
                return

            if type_opt_node and type_opt_node.hijos and type_opt_node.hijos[0].valor == 'Type':
                tipo_retorno_str = extract_data_type_from_type_node(type_opt_node.hijos[0])

            if not es_hatun_ruray:
                scope_manager.add_symbol(nombre_funcion, tipo_retorno_str, linea_decl_func, symbol_type="funcion")
            
            scope_manager.enter_scope(nombre_funcion)

            if parametros_node and parametros_node.hijos and parametros_node.hijos[0].valor == 'ParamList':
                param_list_node = parametros_node.hijos[0]
                if not (param_list_node.hijos and len(param_list_node.hijos) == 2 and \
                        param_list_node.hijos[0].valor == 'Param' and \
                        param_list_node.hijos[1].valor == 'ParamTail'):
                    print(f"Error Crítico AST: Estructura de ParamList incorrecta. Hijos: {[h.valor for h in param_list_node.hijos] if param_list_node.hijos else 'ninguno'}")
                else:
                    current_P_node = param_list_node.hijos[0]
                    current_PT_node = param_list_node.hijos[1]
                    while True:
                        if current_P_node.valor == 'Param' and len(current_P_node.hijos) == 3:
                            param_type_container_node = current_P_node.hijos[0]
                            param_name_node = current_P_node.hijos[2]
                            if param_type_container_node.valor == 'Type' and param_name_node.valor == 'IDENTIFICADOR_TOKEN':
                                param_name = get_node_value(param_name_node)
                                param_type_str = extract_data_type_from_type_node(param_type_container_node)
                                linea_decl_param = get_node_line(param_name_node)
                                scope_manager.add_symbol(param_name, param_type_str, linea_decl_param, symbol_type="parametro")
                            else:
                                print(f"Error Crítico AST: Estructura interna de Param incorrecta. Type: '{param_type_container_node.valor}', ID: '{param_name_node.valor}'")
                                break
                        else:
                            print(f"Error Crítico AST: Se esperaba nodo Param. Se obtuvo: '{current_P_node.valor}'")
                            break
                        
                        if current_PT_node.hijos and len(current_PT_node.hijos) == 3 and \
                           current_PT_node.hijos[0].valor == 'COMA_TOKEN' and \
                           current_PT_node.hijos[1].valor == 'Param' and \
                           current_PT_node.hijos[2].valor == 'ParamTail':
                            current_P_node = current_PT_node.hijos[1]
                            current_PT_node = current_PT_node.hijos[2]
                        elif not current_PT_node.hijos or \
                             (len(current_PT_node.hijos) == 1 and current_PT_node.hijos[0].valor == 'epsilon_node'):
                            break 
                        else:
                            print(f"Error Crítico AST: Estructura de ParamTail inesperada. Hijos: {[h.valor for h in current_PT_node.hijos] if current_PT_node.hijos else 'ninguno'}")
                            break
            
            if block_node:
                visit(block_node)
            
            scope_manager.exit_scope()

        elif node_type == 'Block':
            if node.hijos and len(node.hijos) == 3 and node.hijos[1].valor == 'InstruccionesOpt':
                visit(node.hijos[1])
            elif node.hijos and len(node.hijos) > 1 and node.hijos[0].valor == 'LLAVE_ABRE' and node.hijos[1].valor == 'InstruccionesOpt':
                 visit(node.hijos[1])

        elif node_type == 'InstruccionesOpt':
            if node.hijos and node.hijos[0].valor == 'Instruccion':
                visit(node.hijos[0]) 
                if len(node.hijos) > 1 and node.hijos[1].valor == 'InstruccionesOpt':
                    visit(node.hijos[1]) 

        elif node_type == 'Instruccion':
            if node.hijos: visit(node.hijos[0]) 

        elif node_type == 'DeclaracionVariable':
            if len(node.hijos) >= 5:
                identificador_node = node.hijos[1]
                type_container_node = node.hijos[2]
                inicializacion_opt_node = node.hijos[3]

                if identificador_node.valor == 'IDENTIFICADOR_TOKEN' and type_container_node.valor == 'Type':
                    variable_name = get_node_value(identificador_node)
                    data_type_str = extract_data_type_from_type_node(type_container_node)
                    linea_declaracion = get_node_line(identificador_node)
                    scope_manager.add_symbol(variable_name, data_type_str, linea_declaracion, symbol_type="variable")
                
                if inicializacion_opt_node.valor == 'InicializacionOpt':
                     visit(inicializacion_opt_node) 
            else:
                print(f"Error Crítico AST: Estructura de DeclaracionVariable inesperada. Hijos: {[h.valor for h in node.hijos] if node.hijos else 'ninguno'}")
        
        elif node_type in ['ParamListOpt', 'TypeOpt', 'InicializacionOpt', 'ParamTail', 'Param', 'Type']:
            for hijo in node.hijos:
                visit(hijo)
        
        elif node_type in ['PALABRA_RESERVADA_RURAY', 'IDENTIFICADOR_TOKEN', 'PARENTESIS_ABRE', 
                           'PARENTESIS_CIERRA', 'LLAVE_ABRE', 'LLAVE_CIERRA', 
                           'PALABRA_RESERVADA_VAR', 'PUNTO_Y_COMA_TOKEN',
                           'DOS_PUNTOS_TOKEN', 'HATUN_RURAY_TOKEN', 'COMA_TOKEN'] or \
             node_type.startswith('TIPO_') or node_type.endswith('_TOKEN'): 
            pass 

        else:
            for hijo in node.hijos:
                visit(hijo)
    
    if 'TOKENS_CON_LEXEMA' not in globals() and 'TOKENS_CON_LEXEMA' not in locals():
        print("Error Crítico: TOKENS_CON_LEXEMA no está definido globalmente.")

    visit(nodo_raiz)

def construir_arbol_sintactico(codigo_fuente_str, ruta_tabla_csv, simbolo_inicial='Program'):
    lista_de_tokens = None
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".ws", encoding='utf-8') as tmp_file:
            tmp_file.write(codigo_fuente_str)
            temp_file_path = tmp_file.name
        
        lista_de_tokens = analyze_file(temp_file_path) 
    except ImportError:
        print("Error Crítico: No se pudo importar 'AnalizadorLexico.analyze_file'.")
        return None
    except Exception as e:
        print(f"Error durante el análisis léxico o al procesar el archivo temporal: {e}")
        return None
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except OSError as e: print(f"Advertencia: No se pudo eliminar el archivo temporal {temp_file_path}: {e}")

    if lista_de_tokens is None:
        print("Error: El análisis léxico no produjo una lista de tokens.")
        return None
    
    tabla_parsing = cargar_tabla_desde_csv(ruta_tabla_csv)
    if tabla_parsing is None:
        print("Error: La tabla de parsing no pudo ser cargada.")
        return None
    
    arbol_sintactico_raiz = parser_ll1(
        lista_de_tokens,
        tabla_parsing,
        start_symbol=simbolo_inicial
    )
    return arbol_sintactico_raiz

def debug_print_ast_structure(node, indent=0):
    if node is None: return
    lexema_str = ""
    try:
        if 'TOKENS_CON_LEXEMA' in globals() and node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
            lexema_str = f" (Lexema: {node.hijos[0].valor})"
    except NameError: 
        pass 

    print("  " * indent + f"Nodo: {node.valor}{lexema_str} (Hijos: {len(node.hijos)})")
    
    for child in node.hijos:
        debug_print_ast_structure(child, indent + 1)

if __name__ == "__main__":
    tabla_csv_path = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv"
    archivo_entrada_path = "E:\\Compiladores\\Inputs\\input1.ws"
    
    codigo_a_parsear = None
    try:
        with open(archivo_entrada_path, 'r', encoding='utf-8') as f_input:
            codigo_a_parsear = f_input.read()
        print(f"--- Contenido leído de '{archivo_entrada_path}' ---")
        print(codigo_a_parsear.strip() if codigo_a_parsear.strip() else "(Archivo vacío)")
        print("---------------------------------------------------")
    except FileNotFoundError:
        print(f"Error: El archivo de entrada '{archivo_entrada_path}' no fue encontrado.")
        exit(1)
    except Exception as e:
        print(f"Error al leer el archivo de entrada '{archivo_entrada_path}': {e}")
        exit(1)

    if not codigo_a_parsear:
        print("El código fuente está vacío. No se puede continuar.")
        exit(1)

    raiz_arbol = construir_arbol_sintactico(codigo_a_parsear, tabla_csv_path, simbolo_inicial='Program')
    
    if raiz_arbol:
        print("\n✅ Análisis sintáctico completado. Árbol generado.")

        print("\n--- Iniciando Análisis Semántico y Construcción de Tabla de Símbolos ---")
        
        if 'TOKENS_CON_LEXEMA' not in globals(): 
            print("ALERTA CRÍTICA: 'TOKENS_CON_LEXEMA' no está definido globalmente.")
        
        scope_manager = ScopeManager()
        analizar_semantica_y_construir_tabla_simbolos(raiz_arbol, scope_manager)
        
        print("\n--- Tabla de Símbolos Generada ---")
        print(scope_manager.get_formatted_symbol_table())
        
    else:
        print("\n❌ Falló el análisis sintáctico. No se generó el árbol.")