'''
Author:     Leonardo Fragoso
System:     Questions Migration Script
Purpose:    Migrate questions from old perguntas.csv to new questions_bank
'''

import csv
import re
import sys
import os

# Add the parent directory to the path to import modules
sys.path.insert(0, os.path.dirname(__file__))

from backend.bot.modules.questions_bank import get_questions_bank

def clean_question_label(label):
    """Remove brackets and options from question label to get clean text"""
    # Remove everything inside [ ] including the brackets
    cleaned = re.sub(r'\s*\[.*?\]\s*', '', label)
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()

def extract_options_from_label(label):
    """Extract options list from question label if present"""
    match = re.search(r'\[(.*?)\]', label)
    if match:
        options_text = match.group(1)
        # Split by comma and clean up
        options = [opt.strip().strip('"') for opt in options_text.split('","')]
        # Remove technical parts like <Yes>, <No>
        options = [re.sub(r'<.*?>', '', opt).strip() for opt in options]
        return [opt for opt in options if opt and opt not in ['Selecionar opção', 'Select an option', 'List of phone country codes']]
    return []

def clean_answer(answer, question_type):
    """Clean answer format, especially for radio buttons"""
    if question_type == 'radio':
        # Remove quotes and angular brackets like """Sim"""<Yes>
        answer = answer.strip('"').strip()
        # Extract text before < if present
        match = re.match(r'(.+?)<', answer)
        if match:
            return match.group(1).strip('"')
    return answer

def migrate_questions(csv_path, questions_bank):
    """Migrate questions from CSV to questions bank"""
    print(f"\n{'='*60}")
    print("🔄 Iniciando Migração de Perguntas do CSV")
    print(f"{'='*60}\n")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Skip empty rows
                    if not row.get('pergunta') or not row.get('resposta'):
                        skipped += 1
                        continue
                    
                    # Extract data
                    raw_label = row['pergunta']
                    raw_answer = row['resposta']
                    question_type = row.get('tipo', 'text')
                    job_title = row.get('vaga', '')
                    company = row.get('empresa', '')
                    
                    # Clean label and extract options
                    clean_label = clean_question_label(raw_label)
                    options = extract_options_from_label(raw_label)
                    clean_answer_text = clean_answer(raw_answer, question_type)
                    
                    # Skip if label is too short or generic
                    if len(clean_label) < 3 or clean_label.lower() in ['telefone', 'e-mail', 'email', 'phone']:
                        skipped += 1
                        continue
                    
                    # Add to questions bank
                    questions_bank.add_question(
                        label=clean_label,
                        answer=clean_answer_text,
                        question_type=question_type,
                        options=options,
                        job_title=f"{job_title} - {company}".strip(' -'),
                        job_id=None
                    )
                    
                    migrated += 1
                    
                    if migrated % 20 == 0:
                        print(f"✅ Migradas {migrated} perguntas...")
                    
                except Exception as e:
                    print(f"⚠️ Erro ao processar pergunta: {e}")
                    errors += 1
                    continue
        
        print(f"\n{'='*60}")
        print("✅ Migração Concluída!")
        print(f"{'='*60}")
        print(f"📊 Estatísticas:")
        print(f"   ✅ Migradas com sucesso: {migrated}")
        print(f"   ⏭️  Ignoradas: {skipped}")
        print(f"   ❌ Erros: {errors}")
        print(f"{'='*60}\n")
        
        # Show stats
        stats = questions_bank.get_statistics()
        print(f"📈 Banco de Perguntas:")
        print(f"   Total de perguntas únicas: {stats['total_questions']}")
        print(f"   Por tipo: {stats['by_type']}")
        print(f"\n💡 Acesse http://localhost:5000 para revisar as perguntas!\n")
        
    except Exception as e:
        print(f"❌ Erro fatal ao ler CSV: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Path to CSV file
    csv_path = r"C:\Users\leona\OneDrive\Documentos\Projetos\linkdin-bot\perguntas.csv"
    
    if not os.path.exists(csv_path):
        print(f"❌ Arquivo CSV não encontrado: {csv_path}")
        sys.exit(1)
    
    # Get questions bank instance
    questions_bank = get_questions_bank()
    
    # Run migration
    success = migrate_questions(csv_path, questions_bank)
    
    sys.exit(0 if success else 1)
