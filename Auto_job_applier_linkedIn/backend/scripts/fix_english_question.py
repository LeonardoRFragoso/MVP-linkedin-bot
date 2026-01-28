'''
Author:     Leonardo Fragoso
System:     Fix English Proficiency Question
Purpose:    Manually fix English proficiency question with complete options
'''

import json
import os

def fix_english_questions():
    """Fix English proficiency questions with complete options"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(script_dir, "data", "questions_bank.json")
    
    print(f"\n{'='*60}")
    print("🔧 Corrigindo Perguntas de Proficiência em Inglês")
    print(f"{'='*60}\n")
    
    # Load questions
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        print(f"✅ Banco carregado: {len(questions)} perguntas")
    except Exception as e:
        print(f"❌ Erro ao carregar: {e}")
        return False
    
    # Known English proficiency options (typical LinkedIn options)
    english_options_pt = ["Nenhuma", "Conversação", "Intermediário", "Proficiente", "Fluente", "Nativo"]
    english_options_en = ["None", "Conversation", "Intermediate", "Proficient", "Fluent", "Native"]
    
    fixed = 0
    
    # Find and fix English proficiency questions
    for q_hash, question in questions.items():
        if question.get('type') == 'select':
            label = question.get('label', '').lower()
            
            # Check if it's an English proficiency question
            if ('proficiência' in label or 'proficiency' in label) and ('inglês' in label or 'english' in label):
                current_options = question.get('options', [])
                original_label = question.get('label', '')
                
                print(f"\n📝 Encontrada: {original_label[:80]}...")
                print(f"   Opções atuais: {current_options}")
                
                # Determine language and set appropriate options
                if 'inglês' in label or 'proficiência' in label:
                    new_options = english_options_pt
                    clean_label = "Qual seu nível de proficiência em Inglês?"
                else:
                    new_options = english_options_en
                    clean_label = "What is your level of proficiency in English?"
                
                # Update question
                question['options'] = new_options
                question['label'] = clean_label
                question['normalized_label'] = clean_label.lower().strip()
                
                print(f"   ✅ CORRIGIDO!")
                print(f"   Novo label: {clean_label}")
                print(f"   Novas opções: {new_options}")
                
                fixed += 1
    
    # Save changes
    if fixed > 0:
        try:
            with open(db_path, 'w', encoding='utf-8') as f:
                json.dump(questions, f, ensure_ascii=False, indent=2)
            print(f"\n{'='*60}")
            print(f"✅ {fixed} perguntas de inglês corrigidas!")
            print(f"{'='*60}\n")
            print("💡 Recarregue http://localhost:5000 para ver as mudanças!\n")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar: {e}")
            return False
    else:
        print("\n⚠️  Nenhuma pergunta de inglês encontrada para corrigir")
        return False

if __name__ == "__main__":
    fix_english_questions()
