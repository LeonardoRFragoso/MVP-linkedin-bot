'''
Author:     Leonardo Fragoso (adapted)
System:     Questions Review Server
Purpose:    Flask server to manage questions bank interface
'''

from flask import Flask, jsonify, request, send_file
from backend.bot.modules.questions_bank import get_questions_bank
import os

app = Flask(__name__)

@app.route('/')
def index():
    return send_file('review_questions.html')

@app.route('/api/questions')
def get_questions():
    """Get all questions and statistics"""
    bank = get_questions_bank()
    questions = bank.export_for_review()
    stats = bank.get_statistics()
    
    return jsonify({
        'questions': questions,
        'stats': stats
    })

@app.route('/api/update_question', methods=['POST'])
def update_question():
    """Update answer for a question"""
    data = request.json
    question_hash = data.get('hash')
    new_answer = data.get('answer')
    
    if not question_hash or new_answer is None:
        return jsonify({'error': 'Missing hash or answer'}), 400
    
    bank = get_questions_bank()
    bank.update_answer(question_hash, new_answer)
    
    return jsonify({'success': True})

@app.route('/api/verify_question', methods=['POST'])
def verify_question():
    """Mark question as verified"""
    data = request.json
    question_hash = data.get('hash')
    verified = data.get('verified', True)
    
    if not question_hash:
        return jsonify({'error': 'Missing hash'}), 400
    
    bank = get_questions_bank()
    bank.mark_verified(question_hash, verified)
    
    return jsonify({'success': True})

@app.route('/api/stats')
def get_stats():
    """Get statistics only"""
    bank = get_questions_bank()
    stats = bank.get_statistics()
    return jsonify(stats)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌐 Servidor de Revisão de Perguntas Iniciado!")
    print("="*60)
    print("\n📋 Acesse o formulário em: http://localhost:5000")
    print("\n💡 Dicas:")
    print("   - Revise e edite as respostas das perguntas")
    print("   - Marque como 'Verificada' após revisar")
    print("   - Use os filtros para encontrar perguntas específicas")
    print("\n⚠️  Para parar o servidor, pressione Ctrl+C")
    print("="*60 + "\n")
    
    app.run(debug=False, host='0.0.0.0', port=5000)
