import os
import re

def is_pure_separator(line):
    line = line.strip()
    return bool(re.match(r'^\|(\s*:?-+:?\s*\|)+$', line))

def is_empty_row(line):
    line = line.strip()
    if not line.startswith('|') or not line.endswith('|'):
        return False
    if is_pure_separator(line):
        return False
    cells = line[1:-1].split('|')
    return all(cell.strip() == '' for cell in cells)

def process_table_block(block):
    if not block:
        return []
    
    # 1. Handle Empty Header + Separator at top
    # If first row is empty and second is separator, and third exists:
    # Transform [Empty, Sep, Data1, ...] -> [Data1, Sep, ...]
    if len(block) >= 3 and is_empty_row(block[0]) and is_pure_separator(block[1]):
        data1 = block[2]
        sep = block[1]
        remaining = block[3:]
        block = [data1, sep] + remaining
    
    new_block = []
    separator_count = 0
    
    for i, line in enumerate(block):
        if is_pure_separator(line):
            separator_count += 1
            if separator_count == 1 and i > 0:
                # Keep the first separator only if it follows a row
                new_block.append(line)
            else:
                # Redundant or leading separator
                pass
        elif is_empty_row(line):
            # Already handled leading empty row if possible, 
            # any other empty row is redundant
            pass
        else:
            # Populated data row
            new_block.append(line)
            # If we just added the first data row and haven't seen a separator, 
            # we might need one? No, assume the original had it.
    
    # Final check: Ensure if we have rows, we have a separator at index 1
    if len(new_block) >= 2 and not is_pure_separator(new_block[1]):
        # Search for the first separator we might have skipped
        found_sep = None
        for l in block:
            if is_pure_separator(l):
                found_sep = l
                break
        if found_sep:
            new_block.insert(1, found_sep)
            
    return new_block

def clean_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        new_lines = []
        current_table = []
        changes = 0
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('|') and stripped.endswith('|'):
                current_table.append(line)
            else:
                if current_table:
                    processed = process_table_block(current_table)
                    if len(processed) != len(current_table):
                        changes += 1
                    new_lines.extend(processed)
                    current_table = []
                new_lines.append(line)
        
        # Last table
        if current_table:
            processed = process_table_block(current_table)
            if len(processed) != len(current_table):
                changes += 1
            new_lines.extend(processed)

        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            print(f"Aegis Table Fix: Optimized {filepath}")
            return 1
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
    return 0

def main():
    targets = [
        "/home/wolfman/projects/MD2FastPDF",
        "/home/wolfman/projects/Pirates-Ancients-Corporations"
    ]
    for target in targets:
        if os.path.isdir(target):
            print(f"Aegis Deep Table Repair: {target}")
            for root, dirs, files in os.walk(target):
                if any(p.startswith('.') for p in root.split(os.sep)):
                    continue
                for file in files:
                    if file.endswith('.md'):
                        clean_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
