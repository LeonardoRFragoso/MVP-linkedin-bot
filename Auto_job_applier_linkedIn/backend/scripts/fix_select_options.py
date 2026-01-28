'''
Author:     Leonardo Fragoso
System:     Fix Select Options Script
Purpose:    Extract and save options for SELECT/RADIO questions
'''

import json
import re
import os

def extract_options_from_string(option_string):
    """Extract options from malformed string like: Selecionar opção\", \"Yes\", \"No\","""
    # Remove all backslashes and quotes
    cleaned_string = option_string.replace('\\', '').replace('"', '')
    
    # Split by comma
    parts = cleaned_string.split(',')
    
    options = []
    for part in parts:
        # Clean up the part
        cleaned = part.strip()
        if cleaned and cleaned not in ['Selecionar opção', 'Select an option', 'Seleciona una opción', 'Selecciona una opção', 'Selecciona una opción']:
            options.append(cleaned)
    
    return options

def extract_options_from_label(label):
    """Extract options from label pattern: [ "option1", "option2", ]"""
    # Find text between [ and ] OR [ and ... (truncated labels)
    bracket_match = re.search(r'\[(.*?)(?:\]|\.\.\.)', label)
    if not bracket_match:
        return []
    
    inside_brackets = bracket_match.group(1)
    
    # Extract all quoted strings
    quoted_matches = re.findall(r'"([^"]+)"', inside_brackets)
    if not quoted_matches:
        return []
    
    # Filter out generic options
    filtered = [
        opt.strip() for opt in quoted_matches 
        if opt.strip() and opt.strip() not in [
            'Selecionar opção', 
            'Select an option', 
            'Seleciona una opción',
            'Selecciona una opção',
            'Selecciona una opción'
        ]
    ]
    
    return filtered

def clean_label_remove_brackets(label):
    """Remove [ ... ] part from label"""
    # Remove everything from [ to ]
    cleaned = re.sub(r'\s*\[.*?\]\s*', '', label)
    return cleaned.strip()

def fix_questions_bank(db_path):
    """Fix all SELECT and RADIO questions in the bank"""
    print(f"\n{'='*60}")
    print("🔧 Corrigindo Opções de SELECT e RADIO")
    print(f"{'='*60}\n")
    print(f"📁 Caminho do banco: {db_path}")
    
    # Load questions
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"✅ Banco carregado com {len(questions)} perguntas totais")
    except Exception as e:
        print(f"❌ Erro ao carregar banco: {e}")
        return False
    
    fixed = 0
    skipped = 0
    select_radio_count = 0
    
    # Fix each SELECT/RADIO question
    for q_hash, question in questions.items():
        if question.get('type') in ['select', 'radio']:
            select_radio_count += 1
            label = question.get('label', '')
            current_options = question.get('options', [])
            
            # Check if options are malformed or empty with options in label
            needs_fix = False
            
            # Debug: print first 5 questions
            if select_radio_count <= 5:
                print(f"\n🔍 Analisando pergunta {select_radio_count}:")
                print(f"   Label: {label[:80]}...")
                print(f"   Options array length: {len(current_options)}")
                print(f"   Tem '[' no label: {'[' in label}")
            
            if len(current_options) == 0 and '[' in label:
                # Options are in label but array is empty
                needs_fix = True
                if select_radio_count <= 5:
                    print(f"   ✅ NEEDS FIX: Options vazio mas tem [ no label")
            elif len(current_options) == 1 and ('"' in current_options[0] or ',' in current_options[0]):
                # Malformed: all options in one string
                needs_fix = True
                if select_radio_count <= 5:
                    print(f"   ✅ NEEDS FIX: Options malformado (string única)")
            elif select_radio_count <= 5:
                print(f"   ⏭️  SKIP: Já está correto")
            
            if needs_fix:
                extracted_options = []
                
                # First, try to extract from malformed options array
                if len(current_options) == 1:
                    extracted_options = extract_options_from_string(current_options[0])
                    if select_radio_count <= 5:
                        print(f"   🔧 Tentando extrair de options[0]: {extracted_options}")
                
                # If that didn't work, try to extract from label
                if not extracted_options:
                    extracted_options = extract_options_from_label(label)
                    if select_radio_count <= 5:
                        print(f"   🔧 Tentando extrair do label: {extracted_options}")
                
                if extracted_options:
                    question['options'] = extracted_options
                    # Clean label by removing bracket part
                    question['label'] = clean_label_remove_brackets(label)
                    question['normalized_label'] = clean_label_remove_brackets(label).lower().strip()
                    fixed += 1
                    if select_radio_count <= 5:
                        print(f"   ✅ CORRIGIDO! Opções: {extracted_options}")
                    else:
                        print(f"✅ '{label[:60]}...'")
                        print(f"   Opções: {extracted_options}")
                else:
                    skipped += 1
                    if select_radio_count <= 5:
                        print(f"   ❌ FALHOU: Não conseguiu extrair opções")
            else:
                skipped += 1
    
    # Save fixed questions
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"\n{'='*60}")
        print("✅ Correção Concluída!")
        print(f"{'='*60}")
        print(f"📊 Estatísticas:")
        print(f"   🔧 Perguntas corrigidas: {fixed}")
        print(f"   ⏭️  Já estavam corretas: {skipped}")
        print(f"   📝 Total SELECT/RADIO: {select_radio_count}")
        print(f"{'='*60}\n")
        print("💡 Recarregue http://localhost:5000 para ver as mudanças!\n")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar banco: {e}")
        return False

if __name__ == "__main__":
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "data", "questions_bank.json")
    
    print(f"🔍 Procurando banco em: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"❌ Arquivo não encontrado: {db_path}")
        print(f"📂 Diretório atual: {os.getcwd()}")
        exit(1)
    
    success = fix_questions_bank(db_path)
    exit(0 if success else 1)
