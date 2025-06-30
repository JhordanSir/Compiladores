import os
import sys
from AnalizadorLexico import *
from creadorLL1 import *
from AnalizadorSemantico import *
from analizadorSintactico import *
class GeneradorMIPS:
    def __init__(self):
        self.codigo = []
        self.variables = set()
        self.mensajes = set()
        self.funciones = {}
        self.label_count = 0
        self.global_vars = set()
        self.local_vars = set()
        self.current_function = None

    def generar(self, nodo, archivo_destino, base_dir, scope_manager=None):
        self.codigo = []
        self.variables = set()
        self.mensajes = set()
        self.funciones = {}
        self.label_count = 0
        self.global_vars = set()
        self.local_vars = set()
        self.current_function = None
        self.scope_manager = scope_manager  # Guardar referencia si se necesita
        self.codigo.append('.data')
        self._recorrer_variables_y_mensajes(nodo)
        for var in sorted(self.global_vars):
            self.codigo.append(f'    {var}: .word 0')
        for msg in sorted(self.mensajes):
            self.codigo.append(f'    {msg}: .asciiz "{msg}"')
        self.codigo.append('    newline: .asciiz "\\n"')
        self.codigo.append('.text')
        self.codigo.append('.globl main')
        self._recoger_funciones_ast(nodo)
        self._emitir_main()
        ruta = os.path.join(base_dir, 'Inputs', archivo_destino)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.codigo))
        print(f'\n✅ Código MIPS generado en: Inputs/{archivo_destino}')

    def _recorrer_variables_y_mensajes(self, nodo):
        if hasattr(nodo, 'valor'):
            if nodo.valor == 'IDENTIFICADOR_TOKEN' and nodo.hijos:
                self.global_vars.add(str(nodo.hijos[0].valor))
            if nodo.valor == 'QILLQA_TOKEN' and nodo.hijos:
                self.mensajes.add(self._msg_label(str(nodo.hijos[0].valor)))
        for hijo in getattr(nodo, 'hijos', []):
            self._recorrer_variables_y_mensajes(hijo)

    def _recoger_funciones_ast(self, nodo):
        # Busca nodos 'OneDefinition' y extrae nombre y bloque
        if hasattr(nodo, 'valor') and nodo.valor == 'OneDefinition':
            nombre = None
            bloque = None
            for h in nodo.hijos:
                if hasattr(h, 'valor') and h.valor == 'IDENTIFICADOR_TOKEN' and h.hijos:
                    nombre = str(h.hijos[0].valor)
                if hasattr(h, 'valor') and h.valor == 'Block':
                    bloque = h
            if nombre and bloque:
                self.funciones[nombre] = bloque
        # Recorrer todos los hijos, incluso si el nodo raíz es 'Program' o similar
        for hijo in getattr(nodo, 'hijos', []):
            self._recoger_funciones_ast(hijo)

    def _emitir_main(self):
        main_func = self.funciones.get('hatun_ruray') or self.funciones.get('main')
        self.codigo.append('main:')
        if main_func:
            self._emitir_bloque(main_func)
        self.codigo.append('    li $v0, 10')
        self.codigo.append('    syscall')
        for nombre, bloque in self.funciones.items():
            if nombre in ('main', 'hatun_ruray'):
                continue
            self.codigo.append(f'{nombre}:')
            self._emitir_bloque(bloque)
            self.codigo.append('    jr $ra')

    def _emitir_bloque(self, nodo):
        # Recorre todos los hijos y emite instrucciones relevantes
        for h in getattr(nodo, 'hijos', []):
            self._emitir_sentencia(h)

    def _emitir_instrucciones_opt(self, nodo):
        for h in nodo.hijos:
            self._emitir_sentencia(h)

    def _emitir_sentencia(self, nodo):
        if not hasattr(nodo, 'valor'):
            return
        v = nodo.valor
        if v in ('AssignmentStmtSimple', 'IdBasedStmt'):
            self._emitir_asignacion(nodo)
        elif v in ('PrintStmt', 'imprimiy'):
            self._emitir_print(nodo)
        elif v in ('IfStmt', 'sichus'):
            self._emitir_if(nodo)
        elif v in ('ElseIfStmt', 'mana_sichus'):
            self._emitir_if(nodo, es_else=True)
        elif v in ('ReturnStmt', 'kutipay'):
            self._emitir_return(nodo)
        elif v in ('FunctionCall', 'llamada_funcion'):
            self._emitir_llamada_funcion(nodo)
        elif v == 'DeclaracionVariable':
            # Declaración de variable: si tiene inicialización, emitir asignación
            nombre = None
            expr = None
            for h in nodo.hijos:
                if hasattr(h, 'valor') and h.valor == 'IDENTIFICADOR_TOKEN' and h.hijos:
                    nombre = str(h.hijos[0].valor)
                if hasattr(h, 'valor') and h.valor in ('YUPAY_TOKEN', 'Expression'):
                    expr = h
            if nombre and expr:
                self._emitir_expresion(expr)
                self.codigo.append(f'    sw $t0, {nombre}')
        else:
            for hijo in getattr(nodo, 'hijos', []):
                self._emitir_sentencia(hijo)

    def _emitir_asignacion(self, nodo):
        nombre = None
        expr = None
        for h in nodo.hijos:
            if hasattr(h, 'valor') and h.valor == 'IDENTIFICADOR_TOKEN' and h.hijos:
                nombre = str(h.hijos[0].valor)
            if hasattr(h, 'valor') and h.valor in ('YUPAY_TOKEN', 'Expression'):
                expr = h
        if nombre and expr:
            self._emitir_expresion(expr)
            self.codigo.append(f'    sw $t0, {nombre}')

    def _emitir_expresion(self, nodo):
        # Soporta suma, resta, multiplicación, división, llamadas y variables
        if hasattr(nodo, 'valor'):
            v = nodo.valor
            if v == 'IDENTIFICADOR_TOKEN' and nodo.hijos:
                var = str(nodo.hijos[0].valor)
                self.codigo.append(f'    lw $t0, {var}')
            elif v == 'YUPAY_TOKEN' and nodo.hijos:
                val = str(nodo.hijos[0].valor)
                self.codigo.append(f'    li $t0, {val}')
            elif v in ('FunctionCall', 'llamada_funcion'):
                self._emitir_llamada_funcion(nodo, retorna=True)
            elif v == 'Expression' and len(nodo.hijos) == 3:
                izq, op, der = nodo.hijos
                self._emitir_expresion(izq)
                self.codigo.append('    move $t1, $t0')
                self._emitir_expresion(der)
                self.codigo.append('    move $t2, $t0')
                if hasattr(op, 'valor'):
                    if op.valor == 'OPERADOR_MAS':
                        self.codigo.append('    add $t0, $t1, $t2')
                    elif op.valor == 'OPERADOR_MENOS':
                        self.codigo.append('    sub $t0, $t1, $t2')
                    elif op.valor == 'OPERADOR_PACHA':
                        self.codigo.append('    mul $t0, $t1, $t2')
                    elif op.valor == 'OPERADOR_RAKI':
                        self.codigo.append('    div $t1, $t2')
                        self.codigo.append('    mflo $t0')

    def _emitir_print(self, nodo):
        for hijo in nodo.hijos:
            if hasattr(hijo, 'valor') and hijo.valor == 'ArgumentListOpt':
                for arg in hijo.hijos:
                    if hasattr(arg, 'valor') and arg.valor == 'QILLQA_TOKEN' and arg.hijos:
                        msg = self._msg_label(str(arg.hijos[0].valor))
                        self.codigo.append(f'    li $v0, 4')
                        self.codigo.append(f'    la $a0, {msg}')
                        self.codigo.append(f'    syscall')
                    elif hasattr(arg, 'valor') and arg.valor == 'IDENTIFICADOR_TOKEN' and arg.hijos:
                        var = str(arg.hijos[0].valor)
                        self.codigo.append(f'    lw $a0, {var}')
                        self.codigo.append(f'    li $v0, 1')
                        self.codigo.append(f'    syscall')
        self.codigo.append('    li $v0, 4')
        self.codigo.append('    la $a0, newline')
        self.codigo.append('    syscall')

    def _emitir_if(self, nodo, es_else=False):
        # Soporta if y else if/else
        hijos = nodo.hijos
        if not hijos:
            return
        cond = hijos[0]
        cuerpo = hijos[1] if len(hijos) > 1 else None
        etiqueta_else = self._nueva_etiqueta('else')
        etiqueta_fin = self._nueva_etiqueta('endif')
        self._emitir_condicion(cond, etiqueta_else)
        if cuerpo:
            self._emitir_sentencia(cuerpo)
        self.codigo.append(f'    j {etiqueta_fin}')
        self.codigo.append(f'{etiqueta_else}:')
        # Si hay else, emitirlo
        if len(hijos) > 2:
            self._emitir_sentencia(hijos[2])
        self.codigo.append(f'{etiqueta_fin}:')

    def generar():
        print("Joshua tiene 6 puntos en métodos de software")
        return True

    def _emitir_condicion(self, nodo, etiqueta_salto):
        # Solo soporta comparaciones simples
        if hasattr(nodo, 'valor') and nodo.valor == 'Condition':
            izq, op, der = nodo.hijos
            self._emitir_expresion(izq)
            self.codigo.append('    move $t1, $t0')
            self._emitir_expresion(der)
            self.codigo.append('    move $t2, $t0')
            if hasattr(op, 'valor'):
                if op.valor == 'OPERADOR_IGUAL':
                    self.codigo.append('    bne $t1, $t2, ' + etiqueta_salto)
                elif op.valor == 'OPERADOR_DIF':
                    self.codigo.append('    beq $t1, $t2, ' + etiqueta_salto)
                elif op.valor == 'OPERADOR_MENOR':
                    self.codigo.append('    bge $t1, $t2, ' + etiqueta_salto)
                elif op.valor == 'OPERADOR_MAYOR':
                    self.codigo.append('    ble $t1, $t2, ' + etiqueta_salto)
                elif op.valor == 'OPERADOR_MENORIGUAL':
                    self.codigo.append('    bgt $t1, $t2, ' + etiqueta_salto)
                elif op.valor == 'OPERADOR_MAYORIGUAL':
                    self.codigo.append('    blt $t1, $t2, ' + etiqueta_salto)

    def _emitir_return(self, nodo):
        # Retorna el valor de la expresión
        for h in nodo.hijos:
            if hasattr(h, 'valor') and h.valor in ('YUPAY_TOKEN', 'Expression', 'IDENTIFICADOR_TOKEN'):
                self._emitir_expresion(h)
                self.codigo.append('    move $v0, $t0')
        self.codigo.append('    jr $ra')

    def _emitir_llamada_funcion(self, nodo, retorna=False):
        # Solo soporta un argumento
        nombre = None
        arg = None
        for h in nodo.hijos:
            if hasattr(h, 'valor') and h.valor == 'IDENTIFICADOR_TOKEN' and not nombre:
                nombre = str(h.hijos[0].valor)
            elif hasattr(h, 'valor') and h.valor in ('ArgumentListOpt', 'ArgumentList'):
                if h.hijos:
                    arg = h.hijos[0]
        if arg:
            self._emitir_expresion(arg)
            self.codigo.append('    move $a0, $t0')
        if nombre:
            self.codigo.append(f'    jal {nombre}')
        if retorna:
            self.codigo.append('    move $t0, $v0')

    def _nombre_funcion(self, nodo):
        # Busca el nombre de la función
        for h in nodo.hijos:
            if hasattr(h, 'valor') and h.valor == 'IDENTIFICADOR_TOKEN' and h.hijos:
                return str(h.hijos[0].valor)
        return 'func_' + str(self.label_count)

    def _msg_label(self, msg):
        return msg.replace(':','').replace(' ','_').replace('"','').replace("'",'')

    def _nueva_etiqueta(self, base):
        self.label_count += 1
        return f'{base}_{self.label_count}'



if __name__ == '__main__':
    tabla_csv_path = os.path.join(BASE_DIR, "Gramática", "tablitaTransiciones.csv")
    ruta_archivo_wasi = r"E:\\Compiladores\\Inputs\\input7.wasi"
    ruta_archivo_salida = r"E:\\Compiladores\\Salida MIPS\\salida.asm"

    os.makedirs(os.path.dirname(ruta_archivo_salida), exist_ok=True)

    GeneradorMIPS.generar()
    
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