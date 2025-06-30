import os
import google.generativeai as genai
from dotenv import load_dotenv, dotenv_values # <-- Importa dotenv_values

def configurar_api():
    env_cargado = load_dotenv(override=True)
    config = dotenv_values(".env")
    api_key_desde_os = os.environ.get('GOOGLE_API_KEY')
    api_key = os.getenv("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)

def crear_prompt_wasi(codigo_fuente):
    especificacion_wasi = f"""
    Eres un compilador experto que traduce un lenguaje de alto nivel llamado "WayraSimi" a código ensamblador MIPS.

    **Reglas de Traducción de WayraSimi a MIPS:**

    1.  **Sección de Datos (`.data`):**
        *   Todas las cadenas de texto (para `imprimiy`) deben ser declaradas aquí con etiquetas únicas (ej: `str1: .asciiz "Hola"`) Despues de imprimir el argumento de imprimy debe dar un salto de linea.
        *   Las variables globales también se declaran aquí.

    2.  **Sección de Código (`.text`):**
        *   La función `hatun_ruray` de WayraSimi DEBE ser traducida como la etiqueta `main` en MIPS.
        *   El programa debe terminar con el syscall de salida (código 10).

    3.  **Convención de Llamadas a Funciones:**
        *   Los argumentos se pasan a través de los registros `$a0`, `$a1`, etc.
        *   El valor de retorno se coloca en el registro `$v0`.
        *   El llamador es responsable de guardar los registros `$t0`-`$t9`.
        *   La función llamada es responsable de guardar los registros `$s0`-`$s7` si los usa.
        *   La dirección de retorno `$ra` DEBE ser guardada en la pila al inicio de cualquier función que no sea hoja (que llame a otras funciones).

    4.  **Manejo de la Pila (Stack):**
        *   Cada función debe tener un prólogo y un epílogo.
        *   **Prólogo:**
            *   `addiu $sp, $sp, -N`  # Reservar espacio para variables locales y registros guardados.
            *   `sw $ra, k($sp)`      # Guardar dirección de retorno.
            *   `sw $fp, l($sp)`      # Guardar el frame pointer anterior.
            *   `addiu $fp, $sp, N`   # Establecer el nuevo frame pointer.
        *   **Epílogo:**
            *   `lw $ra, k($sp)`      # Restaurar dirección de retorno.
            *   `lw $fp, l($sp)`      # Restaurar frame pointer anterior.
            *   `addiu $sp, $sp, N`   # Liberar espacio de la pila.
            *   `jr $ra`              # Regresar.

    5.  **Syscalls de MARS/SPIM (importante):**
        *   `imprimiy(entero)` -> `li $v0, 1` + syscall
        *   `imprimiy(flotante)` -> `li $v0, 2` + syscall
        *   `imprimiy("texto")` -> `li $v0, 4` + syscall
        *   `fin del programa` -> `li $v0, 10` + syscall

    6.  **Diccionario de WayraSimi (Quechua -> Español/Inglés):**
        *   `ruray`: define una función (def).
        *   `hatun_ruray`: función principal (main).
        *   `var`: declara una variable (var).
        *   `yupay`: tipo entero (int).
        *   `chiqi`: tipo flotante (float).
        *   `qillqa`: tipo cadena (string).
        *   `chiqap`: tipo booleano (bool).
        *   `chiqaq`: valor Verdadero (True).
        *   `mana_chiqap`: valor Falso (False).
        *   `sichus`: si (if).
        *   `mana_sichus`: sino si (elif/else if).
        *   `mana`: sino (else) / negación lógica (not).
        *   `para`: bucle (for/while).
        *   `kutipay`: retornar (return).
        *   `pakiy`: romper bucle (break).
        *   `imprimiy`: imprimir (print).
        *   `wan`: Y lógico (and).
        *   `utaq`: O lógico (or).

    **Tarea:**
    Traduce el siguiente código WayraSimi a código MIPS. Asegúrate de seguir TODAS las reglas mencionadas. El código MIPS debe ser completo, ejecutable y bien comentado.

    ```wasi
    {codigo_fuente}
    ```

    **Salida esperada:**
    Proporciona ÚNICAMENTE el código MIPS completo en un solo bloque de código. No incluyas explicaciones adicionales fuera del código.
    """
    
    prompt_completo = f"{especificacion_wasi}\n\n--- CÓDIGO WASI A TRADUCIR ---\n\n{codigo_fuente}\n\n--- CÓDIGO MIPS RESULTANTE ---\n"
    return prompt_completo

def traducir_wasi_a_mips(codigo_wasi):
    try:
        configurar_api()
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        prompt = crear_prompt_wasi(codigo_wasi)
                
        response = model.generate_content(prompt)
        
        return response.text.strip()

    except Exception as e:
        return None

if __name__ == "__main__":
    ruta_archivo_wasi = r"E:\\Compiladores\\Inputs\\input2.wasi"
    ruta_archivo_salida = r"E:\\Compiladores\\Salida MIPS\\salida.asm"

    print(f"Leyendo código Wasi desde: {ruta_archivo_wasi}")

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