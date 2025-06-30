# GeneradorCodigo.py

import os
import sys
# La importación de TOKENS_CON_LEXEMA se ha eliminado de aquí
from AnalizadorLexico import analyze_file
from analizadorSintactico import cargar_tabla_desde_csv, parser_ll1, Nodo
from creadorLL1 import *
# Obtenemos el directorio base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# CORRECCIÓN: La constante se define aquí para que el script sea autocontenido
TOKENS_CON_LEXEMA = {
    'IDENTIFICADOR_TOKEN',
    'QILLQA_TOKEN',
    'YUPAY_TOKEN',
    'CHIQI_KAY_TOKEN',
}

# --- Funciones de Ayuda (Copiadas o adaptadas de AnalizadorSemantico.py) ---

def get_node_value(node):
    """Obtiene el valor de un nodo token, que usualmente está en su primer hijo."""
    if node is None: return None
    if node.valor in TOKENS_CON_LEXEMA and node.hijos and node.hijos[0]:
        return node.hijos[0].valor
    return node.valor

def get_node_line(node):
    """Obtiene el número de línea de un nodo, buscando recursivamente si es necesario."""
    if node and hasattr(node, 'token_original') and node.token_original:
        return node.token_original.lineno
    if node and node.hijos:
        for hijo in node.hijos:
            if hasattr(hijo, 'token_original') and hijo.token_original:
                return hijo.token_original.lineno
            if isinstance(hijo, Nodo):
                line = get_node_line(hijo)
                if line != "N/A":
                    return line
    return "N/A"

# --- Clase Principal del Generador de Código ---

class CodeGenerator:
    def __init__(self):
        self.data_section = [".data"]
        self.text_section = [".text"]
        self.label_counter = 0
        self.string_literals = {}
        self.var_to_reg_map = {}
        self.next_available_reg = 0

    def _new_label(self, prefix="L"):
        """Genera una nueva etiqueta única."""
        label = f"{prefix}_{self.label_counter}"
        self.label_counter += 1
        return label

    def _get_reg_for_var(self, var_name):
        """Asigna un registro $t a una variable. Si ya está asignado, lo devuelve."""
        if var_name not in self.var_to_reg_map:
            if self.next_available_reg > 9:
                # Limitación: Solo usamos $t0-$t9. Un compilador real usaría la pila.
                print(f"Error: Se agotaron los registros. No se puede asignar a '{var_name}'.")
                sys.exit(1)
            reg = f"$t{self.next_available_reg}"
            self.var_to_reg_map[var_name] = reg
            self.next_available_reg += 1
        return self.var_to_reg_map[var_name]
    
    def _add_string_literal(self, text):
        """Añade una cadena a la sección .data si no existe y devuelve su etiqueta."""
        if text in self.string_literals:
            return self.string_literals[text]
        
        label = self._new_label("string")
        self.string_literals[text] = label
        # El ensamblador MIPS requiere que los caracteres especiales se escapen
        escaped_text = text.replace("\n", "\\n").replace("\t", "\\t").replace('"', '\"')
        self.data_section.append(f'    {label}: .asciiz "{escaped_text}"')
        return label

    def generate(self, node):
        """Punto de entrada para la generación de código a partir del AST."""
        self._generate_node(node)
        return self.get_full_code()

    def get_full_code(self):
        """Une las secciones .data y .text para formar el código MIPS final."""
        # Agrega un salto de línea si hay datos, para separar visualmente
        data_part = "\n".join(self.data_section)
        if len(self.data_section) > 1:
            data_part += "\n"
            
        return data_part + "\n" + "\n".join(self.text_section)

    def _generate_node(self, node):
        """Función 'visitante' que despacha al método correcto según el tipo de nodo."""
        if node is None or node.valor == 'epsilon_node':
            return

        method_name = f'_generate_{node.valor}'
        if hasattr(self, method_name):
            method = getattr(self, method_name)
            method(node)
        else:
            # Si no hay un método específico, simplemente visitamos a los hijos
            for child in node.hijos:
                self._generate_node(child)
    
    # --- Métodos de Generación Específicos para cada Nodo del AST ---
    
    def _generate_OneDefinition(self, node):
        # Asumimos que la función principal es 'hatun_ruray'
        # OneDefinition -> (HATUN_RURAY_TOKEN | IDENTIFICADOR_TOKEN) ...
        first_child = node.hijos[0]
        if first_child.valor == 'HATUN_RURAY_TOKEN' or \
           (first_child.valor == 'IDENTIFICADOR_TOKEN' and get_node_value(first_child) == 'hatun_ruray'):
            
            self.text_section.append("main:")
            
            # El nodo Block está en diferentes posiciones dependiendo de si es hatun_ruray o una función normal
            block_node = None
            if first_child.valor == 'HATUN_RURAY_TOKEN':
                block_node = node.hijos[3] # hatun_ruray() { Block }
            else:
                block_node = node.hijos[5] # ruray func() { Block }

            if block_node:
                self._generate_node(block_node)

            # Código de finalización del programa
            self.text_section.append("\n    # Fin del programa")
            self.text_section.append("    li $v0, 10")
            self.text_section.append("    syscall")

    def _generate_DeclaracionVariable(self, node):
        # Ejemplo de nodo: ['PALABRA_RESERVADA_VAR', 'IDENTIFICADOR_TOKEN', 'Type', 'InicializacionOpt', 'PUNTO_Y_COMA_TOKEN']
        var_name = get_node_value(node.hijos[1])
        register = self._get_reg_for_var(var_name)
        
        inicializacion_opt_node = node.hijos[3]
        if inicializacion_opt_node.hijos and inicializacion_opt_node.hijos[0].valor != 'epsilon_node':
            # Hay una inicialización: = Expression
            expression_node = inicializacion_opt_node.hijos[1]
            
            # Simplificación: Asumimos que la expresión es un literal simple.
            # Un generador completo evaluaría expresiones complejas aquí.
            try:
                # Navegación profunda y frágil. Una mejor AST ayudaría.
                unidad_node = expression_node.hijos[0].hijos[0].hijos[0].hijos[0].hijos[0]
                literal_value_node = unidad_node.hijos[0].hijos[0]
                literal_value = get_node_value(literal_value_node)
                
                self.text_section.append(f"    # var {var_name} = {literal_value}")
                self.text_section.append(f"    li {register}, {literal_value}")
            except (IndexError, AttributeError):
                print(f"ADVERTENCIA: No se pudo generar la inicialización para la variable '{var_name}'. Estructura de expresión no esperada.")


    def _generate_IfStmt(self, node):
        # ['PALABRA_RESERVADA_SICHUS', 'PARENTESIS_ABRE', 'Expression', 'PARENTESIS_CIERRA', 'Block', 'ElsePart']
        condition_node = node.hijos[2]
        if_block_node = node.hijos[4]
        else_part_node = node.hijos[5]
        has_else_block = else_part_node.hijos and else_part_node.hijos[0].valor != 'epsilon_node'

        # Generar etiquetas para if, else y fin del if
        if_true_label = self._new_label("IF_TRUE")
        end_if_label = self._new_label("END_IF")
        
        # Generar código para la condición
        self._generate_conditional_branch(condition_node, if_true_label)
        
        # --- Generar bloque ELSE (si la condición es falsa) ---
        if has_else_block:
            self.text_section.append(f"\n    # Bloque MANA (ELSE)")
            # ElsePart -> (PALABRA_RESERVADA_MANA | PALABRA_RESERVADA_MANA_SICHUS) ...
            # Simplificando, solo manejamos 'mana' simple por ahora
            if else_part_node.hijos[0].valor == 'PALABRA_RESERVADA_MANA':
                else_block_node = else_part_node.hijos[1] 
                self._generate_node(else_block_node)

        # Saltar al final del if-else para no ejecutar el bloque IF
        self.text_section.append(f"    j {end_if_label}")

        # --- Generar bloque IF (si la condición es verdadera) ---
        self.text_section.append(f"\n{if_true_label}:")
        self.text_section.append(f"    # Bloque SICHUS (IF)")
        self._generate_node(if_block_node)

        # Etiqueta final
        self.text_section.append(f"\n{end_if_label}:")

    def _generate_conditional_branch(self, condition_node, true_label):
        """Genera el código de salto para una condición."""
        try:
            term_logico_node = condition_node.hijos[0]
            term_comp_node = term_logico_node.hijos[0]
            
            # Obtenemos operandos y operador
            left_operand_node = term_comp_node.hijos[0] # SumaRestaTerm
            term_logico_conti_node = term_logico_node.hijos[1]
            
            # Si no hay continuación lógica, es una comparación simple
            if term_logico_conti_node.hijos[0].valor == 'epsilon_node':
                comp_conti_node = term_comp_node.hijos[1]
                op_node = comp_conti_node.hijos[0]
                right_operand_node = comp_conti_node.hijos[1]
                
                reg1 = self._get_operand_register(left_operand_node)
                reg2 = self._get_operand_register(right_operand_node)

                operator = op_node.hijos[0].valor
                
                branch_instructions = {
                    'OPERADOR_MAYOR': 'bgt', 'OPERADOR_MENOR': 'blt',
                    'OPERADOR_MAYOR_IGUAL': 'bge', 'OPERADOR_MENOR_IGUAL': 'ble',
                    'OPERADOR_IGUALDAD': 'beq', 'OPERADOR_MANA_IGUAL': 'bne'
                }

                if operator in branch_instructions:
                    branch_instr = branch_instructions[operator]
                    self.text_section.append(f"    {branch_instr} {reg1}, {reg2}, {true_label}")
                else:
                    print(f"Error: Operador condicional no soportado '{operator}'")
        except (IndexError, AttributeError):
            print("ADVERTENCIA: Estructura de condición compleja no soportada. Generación de salto fallida.")

    def _get_operand_register(self, operand_node):
        """Devuelve el registro de una variable o carga un literal en un registro temporal."""
        try:
            # Navegación muy específica basada en la gramática
            unidad_node = operand_node.hijos[0].hijos[0]
            if unidad_node.valor == 'OPERADOR_MENOS':
                unidad_node = operand_node.hijos[0].hijos[1]
            child = unidad_node.hijos[0]

            if child.valor == 'ValorUnitario': # Es una variable
                var_name = get_node_value(child.hijos[0])
                return self._get_reg_for_var(var_name)
            elif child.valor == 'Dato': # Es un literal
                literal_value = get_node_value(child.hijos[0])
                # Usamos el registro $at (assembler temporary) para literales
                self.text_section.append(f"    li $at, {literal_value}")
                return "$at"
        except (IndexError, AttributeError):
            print("ADVERTENCIA: No se pudo resolver el operando en la condición.")

        return "$zero" # Valor por defecto en caso de fallo

    def _generate_PrintStmt(self, node):
        # ['PALABRA_RESERVADA_IMPRIMIY', 'PARENTESIS_ABRE', 'ArgumentListOpt', 'PARENTESIS_CIERRA', 'PUNTO_Y_COMA_TOKEN']
        args_node = node.hijos[2]

        if args_node.hijos and args_node.hijos[0].valor != 'epsilon_node':
            # Asumimos un solo argumento que es una cadena literal.
            expression_node = args_node.hijos[0]
            try:
                # La navegación puede ser frágil, depende de la estructura exacta del AST
                unidad_node = expression_node.hijos[0].hijos[0].hijos[0].hijos[0].hijos[0]
                string_literal_node = unidad_node.hijos[0].hijos[0]
                string_value = get_node_value(string_literal_node)
                
                string_label = self._add_string_literal(string_value)

                self.text_section.append(f"\n    # imprimiy(\"{string_value}\")")
                self.text_section.append(f"    la $a0, {string_label}")
                self.text_section.append("    li $v0, 4")
                self.text_section.append("    syscall")

            except (IndexError, AttributeError):
                 print(f"ADVERTENCIA: La estructura para 'imprimiy' no es la esperada. Solo se soportan cadenas literales simples.")


if __name__ == '__main__':
    tabla_csv_path = os.path.join(BASE_DIR, "Gramática", "tablitaTransiciones.csv")
    ruta_archivo_wasi = r"E:\\Compiladores\\Inputs\\input2.wasi"
    ruta_archivo_salida = r"E:\\Compiladores\\Salida MIPS\\salida.asm"

    os.makedirs(os.path.dirname(ruta_archivo_salida), exist_ok=True)
    
    print("--- 1. Análisis Léxico y Sintáctico ---")
    
    lista_de_tokens = analyze_file(ruta_archivo_wasi)

    if not lista_de_tokens:
        print("\n❌ Error durante el análisis léxico o el archivo está vacío.")
        sys.exit(1)
        
    tabla_parsing = cargar_tabla_desde_csv(tabla_csv_path)
    if tabla_parsing is None:
        print("\n❌ No se pudo continuar debido a un error al cargar la tabla de parsing.")
        sys.exit(1)

    raiz_arbol_sintactico = parser_ll1(lista_de_tokens, tabla_parsing, start_symbol='Program')

    if raiz_arbol_sintactico:
        print("\n✅ Árbol de sintaxis generado correctamente.")
        
        print("\n--- 2. Generación de Código MIPS ---")
        
        try:
            with open(ruta_archivo_wasi, 'r', encoding='utf-8') as f:
                codigo_fuente_wasi = f.read()
            
            if not codigo_fuente_wasi.strip():
                print("El archivo de entrada está vacío.")
            else:
                print("Código fuente leído correctamente.")
                
                codigo_assembler = traducir_wasi_a_mips(codigo_fuente_wasi)
                
                if codigo_assembler:
                    print("\n--- CÓDIGO ASSEMBLER GENERADO ---")
                    print(codigo_assembler)
                    print("---------------------------------")
                    
                    try:
                        with open(ruta_archivo_salida, 'w', encoding='utf-8') as f_out:
                            f_out.write(codigo_assembler)
                        print(f"\n✅ Código assembler guardado exitosamente en: {ruta_archivo_salida}")
                    except IOError as e:
                        print(f"\n❌ Error al guardar el archivo de salida: {e}")
                else:
                    print("\n❌ No se pudo generar el código assembler.")

        except FileNotFoundError:
            print(f"❌ Error: No se encontró el archivo de entrada en la ruta: {ruta_archivo_wasi}")
        except Exception as e:
            print(f"❌ Ha ocurrido un error inesperado: {e}")

        print("✅ Código MIPS generado.")
        
    else:
        print("\n❌ Falló el análisis sintáctico. No se puede generar código.")