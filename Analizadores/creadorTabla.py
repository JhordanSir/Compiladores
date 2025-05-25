import csv
from collections import defaultdict

EPSILON_SYMBOL = "''" # Cómo representas epsilon en tu gramática de entrada
EPSILON_OUTPUT_STRING = "epsilon" # Cómo quieres que se vea epsilon en el CSV de salida
EOF_SYMBOL = "$"

def parse_grammar(grammar_lines):
    grammar = defaultdict(list)
    non_terminals = set()
    terminals = set()
    start_symbol = None
    all_symbols_in_order = [] # Para mantener el orden de los no terminales

    for line in grammar_lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "->" not in line:
            continue

        lhs, rhs_str = line.split("->", 1)
        lhs = lhs.strip()
        if lhs not in non_terminals: # Para mantener el orden de aparición
            all_symbols_in_order.append(lhs)
        non_terminals.add(lhs)


        if start_symbol is None:
            start_symbol = lhs

        productions_str = rhs_str.split("|")
        for prod_str in productions_str:
            symbols = [s.strip() for s in prod_str.strip().split()]
            if not symbols or (len(symbols) == 1 and symbols[0] == "''"):
                symbols = [EPSILON_SYMBOL]
            grammar[lhs].append(symbols)

    for nt in grammar:
        for production in grammar[nt]:
            for symbol in production:
                if symbol != EPSILON_SYMBOL and symbol not in non_terminals:
                    terminals.add(symbol)
    
    return grammar, non_terminals, terminals, start_symbol, all_symbols_in_order

def calculate_first_sets(grammar, non_terminals, terminals, epsilon_symbol):
    first = defaultdict(set)
    for t in terminals:
        first[t] = {t}
    first[epsilon_symbol] = {epsilon_symbol}
    for nt in non_terminals:
        first[nt] = set()

    changed = True
    while changed:
        changed = False
        for nt in non_terminals:
            original_first_nt_size = len(first[nt])
            for production in grammar[nt]:
                if production == [epsilon_symbol]:
                    if epsilon_symbol not in first[nt]:
                        first[nt].add(epsilon_symbol)
                        changed = True
                    continue

                can_derive_epsilon_so_far = True
                for symbol_idx, symbol in enumerate(production):
                    current_symbol_first = set(first[symbol]) # Copia para no modificarla si es la misma
                    
                    added_new = False
                    for f_sym in current_symbol_first:
                        if f_sym != epsilon_symbol:
                            if f_sym not in first[nt]:
                                first[nt].add(f_sym)
                                added_new = True
                    if added_new:
                         changed = True
                    
                    if epsilon_symbol not in current_symbol_first:
                        can_derive_epsilon_so_far = False
                        break 
                
                if can_derive_epsilon_so_far:
                    if epsilon_symbol not in first[nt]:
                        first[nt].add(epsilon_symbol)
                        changed = True
    return first

def calculate_follow_sets(grammar, non_terminals, terminals, start_symbol, first_sets, epsilon_symbol, eof_symbol):
    follow = defaultdict(set)
    for nt in non_terminals:
        follow[nt] = set()
    if start_symbol:
        follow[start_symbol].add(eof_symbol)

    changed = True
    while changed:
        changed = False
        for nt_A in non_terminals:
            for production in grammar[nt_A]:
                for i, symbol_B in enumerate(production):
                    if symbol_B in non_terminals:
                        original_follow_B_size = len(follow[symbol_B])
                        
                        beta = production[i+1:]
                        
                        if beta:
                            first_of_beta = set()
                            can_beta_be_epsilon = True
                            for beta_symbol_idx, beta_symbol in enumerate(beta):
                                first_of_beta_symbol = first_sets[beta_symbol]
                                for f_s in first_of_beta_symbol:
                                    if f_s != epsilon_symbol:
                                        first_of_beta.add(f_s)
                                if epsilon_symbol not in first_of_beta_symbol:
                                    can_beta_be_epsilon = False
                                    break
                            
                            for f_s_beta in first_of_beta: # No añadir epsilon de first_of_beta
                                if f_s_beta not in follow[symbol_B]:
                                    follow[symbol_B].add(f_s_beta)
                                    # changed = True # El cambio se detecta al final

                            if can_beta_be_epsilon or not beta: # si beta puede ser epsilon o beta es vacía
                                for f_s_A in follow[nt_A]:
                                    if f_s_A not in follow[symbol_B]:
                                        follow[symbol_B].add(f_s_A)
                                        # changed = True # El cambio se detecta al final
                        else: # beta es vacía, A -> alpha B
                            for f_s_A in follow[nt_A]:
                                if f_s_A not in follow[symbol_B]:
                                    follow[symbol_B].add(f_s_A)
                                    # changed = True # El cambio se detecta al final
                        
                        if len(follow[symbol_B]) > original_follow_B_size:
                            changed = True
    return follow

def create_ll1_parsing_table(grammar, non_terminals, first_sets, follow_sets, epsilon_symbol, eof_symbol):
    parsing_table = defaultdict(dict)
    conflicts = []

    for nt_A in non_terminals:
        for production_alpha in grammar[nt_A]:
            first_of_alpha = set()
            can_alpha_be_epsilon = True

            if production_alpha == [epsilon_symbol]:
                first_of_alpha.add(epsilon_symbol)
            else:
                for symbol in production_alpha:
                    current_symbol_first = first_sets[symbol]
                    for f_sym in current_symbol_first:
                        if f_sym != epsilon_symbol:
                            first_of_alpha.add(f_sym)
                    if epsilon_symbol not in current_symbol_first:
                        can_alpha_be_epsilon = False
                        break
                if can_alpha_be_epsilon:
                    first_of_alpha.add(epsilon_symbol)
            
            for terminal_a in first_of_alpha:
                if terminal_a != epsilon_symbol:
                    if terminal_a in parsing_table[nt_A]:
                        conflict_msg = (f"Conflicto LL(1) en M[{nt_A}, {terminal_a}]: "
                                        f"Existente: {nt_A} -> {' '.join(parsing_table[nt_A][terminal_a])}, "
                                        f"Nuevo: {nt_A} -> {' '.join(production_alpha)}")
                        print(conflict_msg)
                        conflicts.append(conflict_msg)
                        # Se queda con la primera regla encontrada para el CSV, o marca CONFLICTO
                        # Para parecerse a tu tabla, nos quedamos con la primera.
                        # Si quieres marcarlo, podrías hacer: parsing_table[nt_A][terminal_a] = ["CONFLICT"]
                    else:
                        parsing_table[nt_A][terminal_a] = production_alpha

            if epsilon_symbol in first_of_alpha:
                for terminal_b in follow_sets[nt_A]:
                    if terminal_b in parsing_table[nt_A]:
                        # Si ya hay una regla (no por epsilon), es un conflicto.
                        # Si la regla existente también era por epsilon, y es diferente, también conflicto.
                        if parsing_table[nt_A][terminal_b] != production_alpha:
                            conflict_msg = (f"Conflicto LL(1) (epsilon) en M[{nt_A}, {terminal_b}]: "
                                            f"Existente: {nt_A} -> {' '.join(parsing_table[nt_A][terminal_b])}, "
                                            f"Nuevo: {nt_A} -> {' '.join(production_alpha)} (por epsilon y FOLLOW)")
                            print(conflict_msg)
                            conflicts.append(conflict_msg)
                    else:
                        parsing_table[nt_A][terminal_b] = production_alpha
    return parsing_table, conflicts

def save_table_to_csv_custom_format(parsing_table, ordered_non_terminals, all_terminals_with_eof, output_filename):
    # Obtener todos los terminales únicos de la cabecera de tu tabla de ejemplo si es posible
    # o usar los calculados y ordenarlos.
    # Para este ejemplo, usaremos los calculados y ordenados alfabéticamente.
    # Si tienes una lista fija de columnas de tu tabla original, puedes usarla aquí.
    
    # Ordenar terminales alfabéticamente, con $ al final si está presente
    sorted_terminals = sorted(list(t for t in all_terminals_with_eof if t != EOF_SYMBOL))
    if EOF_SYMBOL in all_terminals_with_eof:
        sorted_terminals.append(EOF_SYMBOL)

    with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        
        header = [''] + sorted_terminals # Primera celda de cabecera vacía
        writer.writerow(header)
        
        for nt in ordered_non_terminals: # Usar el orden de aparición de los no terminales
            row = [nt]
            for t in sorted_terminals:
                production_symbols = parsing_table[nt].get(t)
                if production_symbols:
                    if production_symbols == [EPSILON_SYMBOL]:
                        row.append(EPSILON_OUTPUT_STRING)
                    else:
                        # Si hay un conflicto y guardaste ["CONFLICT"], lo escribes
                        if production_symbols == ["CONFLICT"]:
                             row.append("CONFLICT")
                        else:
                             row.append(' '.join(production_symbols))
                else:
                    row.append('') # Celda vacía
            writer.writerow(row)
    print(f"Tabla de parsing LL(1) (formato custom) guardada en {output_filename}")


def main():
    grammar_filepath = "E:\\Compiladores\\Gramática\\GramaticaLL1.bnf" 
    output_csv_filepath = "E:\\Compiladores\\Gramática\\tablitaTransiciones.csv" # Nuevo nombre para no sobrescribir

    try:
        with open(grammar_filepath, 'r', encoding='utf-8') as f:
            grammar_lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de gramática '{grammar_filepath}'")
        return

    grammar, non_terminals, terminals, start_symbol, ordered_non_terminals = parse_grammar(grammar_lines)
    
    if not start_symbol:
        print("Error: No se pudo determinar el símbolo inicial.")
        return

    print("--- Gramática Parseada ---")
    for nt in ordered_non_terminals:
        prods = grammar[nt]
        print(f"  {nt} -> {prods}")
    # print(f"No Terminales: {non_terminals}")
    # print(f"Terminales: {terminals}")
    # print(f"Símbolo Inicial: {start_symbol}\n")

    first_sets = calculate_first_sets(grammar, non_terminals, terminals, EPSILON_SYMBOL)
    print("\n--- Conjuntos FIRST ---")
    for symbol in list(non_terminals) + list(terminals) + [EPSILON_SYMBOL]:
        if symbol in first_sets: # Solo imprimir si existe
             print(f"  FIRST({symbol}) = {first_sets[symbol]}")
    

    follow_sets = calculate_follow_sets(grammar, non_terminals, terminals, start_symbol, first_sets, EPSILON_SYMBOL, EOF_SYMBOL)
    print("\n--- Conjuntos FOLLOW ---")
    for nt in ordered_non_terminals:
        print(f"  FOLLOW({nt}) = {follow_sets[nt]}")
    

    parsing_table, conflicts_found = create_ll1_parsing_table(grammar, non_terminals, first_sets, follow_sets, EPSILON_SYMBOL, EOF_SYMBOL)
    
    if conflicts_found:
        print("\n--- CONFLICTOS LL(1) DETECTADOS ---")
        for conflict in conflicts_found:
            print(f"  {conflict}")
    else:
        print("\n--- No se detectaron conflictos LL(1). La gramática podría ser LL(1). ---")

    all_terminals_for_header = terminals.copy()
    all_terminals_for_header.add(EOF_SYMBOL)
    
    save_table_to_csv_custom_format(parsing_table, ordered_non_terminals, all_terminals_for_header, output_csv_filepath)

if __name__ == "__main__":
    main()