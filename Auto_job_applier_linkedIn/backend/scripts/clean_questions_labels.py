'''
Author:     Leonardo Fragoso
System:     Questions Cleanup Script
Purpose:    Clean up question labels removing technical prefixes
'''

import json
import sys
import os
import re

def clean_question_label(label):
    """Remove technical prefixes and clean up labels"""
    # Remove direct- prefixes
    label = re.sub(r'^direct-[a-z]+:', '', label, flags=re.IGNORECASE)
    
    # Remove extra whitespace
    label = ' '.join(label.split())
    
    # Capitalize first letter
    if label:
        label = label[0].upper() + label[1:]
    
    return label.strip()

def clean_questions_bank(db_path):
    """Clean all questions in the bank"""
    print(f"\n{'='*60}")
    print("🧹 Limpando Labels das Perguntas")
    print(f"{'='*60}\n")
    
    # Load questions
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao carregar banco: {e}")
        return False
    
    cleaned = 0
    skipped = 0
    
    # Clean each question
    for q_hash, question in questions.items():
        original_label = question.get('label', '')
        cleaned_label = clean_question_label(original_label)
        
        if cleaned_label != original_label:
            question['label'] = cleaned_label
            # Update normalized label too
            question['normalized_label'] = cleaned_label.lower().strip()
            cleaned += 1
            print(f"✅ '{original_label[:60]}...' -> '{cleaned_label[:60]}...'")
        else:
            skipped += 1
    
    # Save cleaned questions
    try:
        with open(db_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print(f"\n{'='*60}")
        print("✅ Limpeza Concluída!")
        print(f"{'='*60}")
        print(f"📊 Estatísticas:")
        print(f"   🧹 Labels limpos: {cleaned}")
        print(f"   ⏭️  Já estavam corretos: {skipped}")
        print(f"   📝 Total: {len(questions)}")
        print(f"{'='*60}\n")
        print("💡 Recarregue http://localhost:5000 para ver as mudanças!\n")
        return True
    except Exception as e:
        print(f"❌ Erro ao salvar banco: {e}")
        return False

if __name__ == "__main__":
    db_path = "data/questions_bank.json"
    
    if not os.path.exists(db_path):
        print(f"❌ Arquivo não encontrado: {db_path}")
        sys.exit(1)
    
    success = clean_questions_bank(db_path)
    sys.exit(0 if success else 1)
