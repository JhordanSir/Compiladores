import csv

def leer_gramatica(archivo):
    with open(archivo, 'r') as f:
        lineas = f.readlines()
    # Filtrar líneas vacías y comentarios
    return [linea.strip() for linea in lineas if linea.strip() and '::=' in linea]

def obtener_no_terminales(gramatica):
    return list({linea.split('::=')[0].strip()[1:-1] for linea in gramatica})

def obtener_terminales(gramatica):
    terminales = set()
    for linea in gramatica:
        if '::=' not in linea:
            continue
        produccion = linea.split('::=')[1]
        # Buscar elementos entre comillas
        partes = produccion.split('"')
        for i in range(1, len(partes), 2):
            if partes[i]:
                terminales.add(partes[i])
    return sorted(list(terminales))

def procesar_produccion(produccion):
    # Dividir por | para obtener alternativas
    alternativas = produccion.split('|')
    resultado = []
    
    for alt in alternativas:
        alt = alt.strip()
        if alt == 'E':
            resultado.append(['epsilon'])
        else:
            elementos = []
            partes = alt.split('"')
            for i, parte in enumerate(partes):
                parte = parte.strip()
                if i % 2 == 0:  # No está entre comillas
                    # Buscar no terminales
                    tokens = [t.strip() for t in parte.split() if t.strip()]
                    for token in tokens:
                        if token.startswith('<') and token.endswith('>'):
                            elementos.append(token[1:-1])
                else:  # Está entre comillas
                    elementos.append(parte)
            resultado.append(elementos)
    
    return resultado

def crear_tabla_transiciones(gramatica):
    no_terminales = obtener_no_terminales(gramatica)
    terminales = obtener_terminales(gramatica)
    
    # Crear diccionario para la tabla
    tabla = {nt: {t: '' for t in terminales + ['$']} for nt in no_terminales}
    
    # Procesar cada regla
    for linea in gramatica:
        no_terminal, produccion = [p.strip() for p in linea.split('::=')]
        no_terminal = no_terminal[1:-1]  # Quitar < >
        
        alternativas = procesar_produccion(produccion)
        
        for alt in alternativas:
            if alt == ['epsilon']:
                tabla[no_terminal]['$'] = 'epsilon'
                for t in terminales:
                    if not tabla[no_terminal][t]:
                        tabla[no_terminal][t] = 'epsilon'
            else:
                # Si el primer elemento es terminal
                if alt[0] in terminales:
                    tabla[no_terminal][alt[0]] = ' '.join(alt)
                else:
                    # Si el primer elemento es no terminal
                    tabla[no_terminal][terminales[0]] = ' '.join(alt)

    return tabla, terminales, no_terminales

def guardar_csv(tabla, terminales, no_terminales, archivo_salida):
    with open(archivo_salida, 'w', newline='') as f:
        writer = csv.writer(f)
        # Escribir encabezados
        writer.writerow([''] + terminales + ['$'])
        # Escribir filas
        for nt in no_terminales:
            fila = [nt]
            for t in terminales + ['$']:
                fila.append(tabla[nt][t])
            writer.writerow(fila)

def main(archivo_entrada, archivo_salida):
    # Leer la gramática
    gramatica = leer_gramatica(archivo_entrada)
    
    # Crear la tabla de transiciones
    tabla, terminales, no_terminales = crear_tabla_transiciones(gramatica)
    
    # Guardar la tabla en CSV
    guardar_csv(tabla, terminales, no_terminales, archivo_salida)

if __name__ == '__main__':
    archivo_entrada = "E:\\Compiladores\\Examen Parcial\\GramaticaBNF.txt"
    archivo_salida = "E:\\Compiladores\\Examen Parcial\\tablaTransiciones.csv"
    main(archivo_entrada, archivo_salida)