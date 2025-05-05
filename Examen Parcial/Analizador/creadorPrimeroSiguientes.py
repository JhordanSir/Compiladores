import re
import csv

class GramaticaAnalyzer:
    def __init__(self):
        self.producciones = {}
        self.first = {}
        self.follow = {}
        self.terminales = set()
        self.no_terminales = set()

    def leer_gramatica(self, archivo):
        with open(archivo, 'r', encoding='utf-8') as f:
            contenido = f.read()
        
        # Extraer las reglas de producción
        lineas = contenido.split('\n')
        produccion_actual = None
        
        for linea in lineas:
            if '::=' in linea:
                # Nueva producción
                izquierda, derecha = linea.split('::=')
                izquierda = izquierda.strip()
                if izquierda.startswith('<') and izquierda.endswith('>'):
                    izquierda = izquierda[1:-1]  # Quitar < >
                    produccion_actual = izquierda
                    self.no_terminales.add(produccion_actual)
                    self.producciones[produccion_actual] = []
                    
                    # Procesar la parte derecha
                    self._procesar_produccion(derecha, produccion_actual)
            
            elif '|' in linea and produccion_actual:
                # Producción alternativa
                self._procesar_produccion(linea, produccion_actual)

    def _procesar_produccion(self, texto, produccion_actual):
        # Limpiar y dividir la producción
        partes = texto.split('|')
        for parte in partes:
            parte = parte.strip()
            if parte:
                simbolos = []
                # Encontrar símbolos entre < > o tokens/terminales
                tokens = re.findall(r'<[^>]+>|"[^"]+"|[A-Z_]+_TOKEN', parte)
                for token in tokens:
                    if token.startswith('<') and token.endswith('>'):
                        simbolo = token[1:-1]  # Quitar < >
                        self.no_terminales.add(simbolo)
                    else:
                        simbolo = token.strip('"')
                        self.terminales.add(simbolo)
                    simbolos.append(simbolo)
                
                if simbolos:
                    self.producciones[produccion_actual].append(simbolos)
                elif 'E' in parte:  # Epsilon
                    self.producciones[produccion_actual].append(['epsilon'])
                    self.terminales.add('epsilon')

    def calcular_first(self):
        self.first = {nt: set() for nt in self.no_terminales}
        self.first.update({t: {t} for t in self.terminales})

        while True:
            cambios = False
            for nt in self.no_terminales:
                for produccion in self.producciones[nt]:
                    first_anterior = len(self.first[nt])
                    
                    # Para cada símbolo en la producción
                    todo_epsilon = True
                    for simbolo in produccion:
                        if simbolo == 'epsilon':
                            self.first[nt].add('epsilon')
                            break
                        
                        if simbolo in self.first:
                            self.first[nt].update(self.first[simbolo] - {'epsilon'})
                            if 'epsilon' not in self.first[simbolo]:
                                todo_epsilon = False
                                break
                        else:
                            self.first[nt].add(simbolo)
                            todo_epsilon = False
                            break
                    
                    if todo_epsilon and len(produccion) > 0:
                        self.first[nt].add('epsilon')
                    
                    if len(self.first[nt]) > first_anterior:
                        cambios = True
            
            if not cambios:
                break

    def calcular_follow(self):
        self.follow = {nt: set() for nt in self.no_terminales}
        self.follow['Program'].add('$')  # Símbolo inicial

        while True:
            cambios = False
            for nt in self.no_terminales:
                for produccion in self.producciones[nt]:
                    for i, simbolo in enumerate(produccion):
                        if simbolo in self.no_terminales:
                            follow_anterior = len(self.follow[simbolo])
                            
                            # Si es el último símbolo
                            if i == len(produccion) - 1:
                                self.follow[simbolo].update(self.follow[nt])
                            else:
                                # Calcular FIRST del resto de la producción
                                siguiente = produccion[i + 1]
                                if siguiente in self.first:
                                    self.follow[simbolo].update(self.first[siguiente] - {'epsilon'})
                                    if 'epsilon' in self.first[siguiente]:
                                        self.follow[simbolo].update(self.follow[nt])
                                else:
                                    self.follow[simbolo].add(siguiente)
                            
                            if len(self.follow[simbolo]) > follow_anterior:
                                cambios = True
            
            if not cambios:
                break

    def guardar_csv(self, archivo_salida):
        with open(archivo_salida, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['No Terminal', 'FIRST', 'FOLLOW'])
            
            for nt in sorted(self.no_terminales):
                first_str = ', '.join(sorted(self.first[nt]))
                follow_str = ', '.join(sorted(self.follow[nt]))
                writer.writerow([nt, first_str, follow_str])

def main():
    analizador = GramaticaAnalyzer()
    analizador.leer_gramatica('E:\\Compiladores\\Examen Parcial\\Analizador\\GramaticaBNF.txt')
    analizador.calcular_first()
    analizador.calcular_follow()
    analizador.guardar_csv('E:\\Compiladores\\Examen Parcial\\Tablas\\primerosYsiguientes.csv')

if __name__ == '__main__':
    main()