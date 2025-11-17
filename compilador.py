# -*- coding: utf-8 -*-
"""
Implementação de um Analisador Léxico em Python.

Baseado na lógica de um analisador em C para uma linguagem
similar ao Pascal.

Este código implementa as seguintes funcionalidades:
- Reconhecimento de Palavras Reservadas e Identificadores.
- Reconhecimento de Números (inteiros, reais e notação científica).
- Reconhecimento de Operadores (relacionais, aritméticos, atribuição).
- Reconhecimento de Literais (strings e caracteres).
- Remoção de comentários de bloco: { ... } e (* ... *).
- Contagem de linhas.
"""

import sys

# --- Definição dos Tipos de Tokens -------------------------------------------
# Usamos strings para facilitar a depuração.
(
    ID,          # Identificador (ex: 'minhaVariavel')
    NUM,         # Número (ex: '10', '12.5', '1.0e-5')
    LITERAL,     # Literal string (ex: 'Ola mundo')
    CAR,         # Literal caractere (ex: 'a')
    
    # Palavras Reservadas (exemplos)
    PROGRAM,     # 'PROGRAM'
    VAR,         # 'VAR'
    BEGIN,       # 'BEGIN'
    END,         # 'END'
    IF,          # 'IF'
    THEN,        # 'THEN'
    ELSE,        # 'ELSE'
    WHILE,       # 'WHILE'
    DO,          # 'DO'
    
    # Operadores
    OPASIGNA,    # Atribuição ':='
    OPREL,       # Relacional '<', '>', '<=', '>=', '<>', '='
    OPSUMA,      # Aditivo '+', '-'
    OPMULT,      # Multiplicativo '*', '/'
    
    # Pontuação
    PONTO,       # '.'
    PONTO_VIRG,  # ';'
    VIRGULA,     # ','
    DOIS_PONTOS, # ':'
    ABRE_PAR,    # '('
    FECHA_PAR,   # ')'
    ABRE_COL,    # '['
    FECHA_COL,   # ']'
    
    # Fim de Arquivo
    EOF          # 'EOF'
) = (
    'ID', 'NUM', 'LITERAL', 'CAR',
    'PROGRAM', 'VAR', 'BEGIN', 'END', 'IF', 'THEN', 'ELSE', 'WHILE', 'DO',
    'OPASIGNA', 'OPREL', 'OPSUMA', 'OPMULT',
    'PONTO', 'PONTO_VIRG', 'VIRGULA', 'DOIS_PONTOS', 'ABRE_PAR', 'FECHA_PAR', 'ABRE_COL', 'FECHA_COL',
    'EOF'
)


class Token:
    """
    Classe que representa um Token.
    Armazena o tipo, o lexema (texto) e a linha onde foi encontrado.
    """
    def __init__(self, tipo, lexema, linha):
        self.tipo = tipo
        self.lexema = lexema
        self.linha = linha

    def __repr__(self):
        """Representação em string do Token para depuração."""
        return f"Token({self.tipo}, '{self.lexema}', Linha {self.linha})"


# --- Mapeamento de Palavras Reservadas ---------------------------------------
# Um dicionário para mapear strings de palavras-chave para seus tipos de token.
# Pascal não é case-sensitive, então compararemos em maiúsculo.
RESERVED_KEYWORDS = {
    'PROGRAM': PROGRAM,
    'VAR': VAR,
    'BEGIN': BEGIN,
    'END': END,
    'IF': IF,
    'THEN': THEN,
    'ELSE': ELSE,
    'WHILE': WHILE,
    'DO': DO,
    # Adicione outras palavras reservadas do Pascal aqui
}


class Lexer:
    """
    O Analisador Léxico (Scanner).
    Lê um código-fonte e o divide em uma sequência de Tokens.
    """
    def __init__(self, source_code):
        self.source = source_code
        self.pos = 0  # Posição atual no código
        self.current_char = self.source[self.pos] if self.pos < len(self.source) else None
        self.line = 1  # Contador de linhas (começa em 1)

    def _error(self, message):
        """Função de erro simples."""
        raise Exception(f"Erro Léxico na Linha {self.line}: {message}")

    def _advance(self):
        """
        Avança o ponteiro `pos` e atualiza `current_char`.
        Esta é a principal forma de consumir caracteres.
        """
        if self.current_char == '\n':
            self.line += 1
        
        self.pos += 1
        if self.pos >= len(self.source):
            self.current_char = None  # Indica Fim de Arquivo (EOF)
        else:
            self.current_char = self.source[self.pos]

    def _peek(self):
        """
        "Espia" o próximo caractere sem consumi-lo.
        Muito útil para operadores de múltiplos caracteres (ex: ':=', '<>').
        """
        peek_pos = self.pos + 1
        if peek_pos >= len(self.source):
            return None
        return self.source[peek_pos]

    def _skip_whitespace(self):
        """Pula caracteres de espaço em branco (espaço, tab, newline)."""
        while self.current_char is not None and self.current_char in ' \t\n':
            self._advance()

    def _skip_comment(self):
        """
        Pula blocos de comentário.
        Reconhece os dois tipos: { ... } e (* ... *).
        Retorna True se pulou um comentário, False caso contrário.
        """
        if self.current_char == '{':
            # Comentário do tipo { ... }
            self._advance()  # Consome o '{'
            while self.current_char is not None and self.current_char != '}':
                self._advance()
            
            if self.current_char is None:
                self._error("Comentário '{' não finalizado.")
            
            self._advance()  # Consome o '}'
            return True

        elif self.current_char == '(' and self._peek() == '*':
            # Comentário do tipo (* ... *)
            self._advance()  # Consome o '('
            self._advance()  # Consome o '*'
            
            while self.current_char is not None:
                if self.current_char == '*' and self._peek() == ')':
                    break
                self._advance()
            
            if self.current_char is None:
                self._error("Comentário '(*' não finalizado.")
            
            self._advance()  # Consome o '*'
            self._advance()  # Consome o ')'
            return True
        
        return False

    def _id_or_keyword(self):
        """
        Processa um identificador ou uma palavra-chave.
        """
        lexeme = ""
        start_line = self.line
        
        # A regra do C é: (isalpha) (isalpha | isdigit)*
        # Em Python: (c.isalpha()) (c.isalnum())*
        # (Assumindo que IDs não começam com números, o que é checado antes)
        while self.current_char is not None and (self.current_char.isalnum()):
            # O C original não permite '_' em IDs. Se for necessário,
            # mude para: self.current_char.isalnum() or self.current_char == '_'
            lexeme += self.current_char
            self._advance()
        
        # Verifica se o lexema é uma palavra reservada
        # Usamos .upper() para case-insensitivity
        token_type = RESERVED_KEYWORDS.get(lexeme.upper())
        
        if token_type:
            return Token(token_type, lexeme, start_line)  # É palavra-chave
        else:
            return Token(ID, lexeme, start_line)  # É identificador

    def _number(self):
        """
        Processa um número (int, real, científico).
        Esta é uma máquina de estados finitos, assim como no código C.
        """
        lexeme = ""
        start_line = self.line
        
        # --- Máquina de Estados para Números ---
        # Estado 0: Parte inteira
        # Estado 1: Viu '.', esperando dígito (parte fracionária)
        # Estado 2: Parte fracionária
        # Estado 3: Viu 'e' ou 'E', esperando sinal ou dígito (expoente)
        # Estado 4: Viu 'e+' ou 'e-', esperando dígito
        # Estado 5: Parte do expoente
        
        state = 0
        while True:
            c = self.current_char
            
            if state == 0:  # Parte inteira
                if c and c.isdigit():
                    lexeme += c
                    self._advance()
                elif c == '.':
                    # Lógica do C: "pode vir outro ponto" (caso de array '1..10')
                    if self._peek() == '.':
                        # É um range '..', então o número '1' terminou.
                        break  # Sai para aceitação
                    else:
                        lexeme += c
                        self._advance()
                        state = 1
                elif c and c.lower() == 'e':
                    lexeme += c
                    self._advance()
                    state = 3
                else:
                    break  # Aceitação (fim do número)

            elif state == 1:  # Esperando dígito após '.'
                if c and c.isdigit():
                    lexeme += c
                    self._advance()
                    state = 2
                else:
                    self._error(f"Dígito esperado após '.' no número '{lexeme}'")

            elif state == 2:  # Parte fracionária
                if c and c.isdigit():
                    lexeme += c
                    self._advance()
                elif c and c.lower() == 'e':
                    lexeme += c
                    self._advance()
                    state = 3
                else:
                    break  # Aceitação

            elif state == 3:  # Viu 'e', esperando sinal ou dígito
                if c in '+-':
                    lexeme += c
                    self._advance()
                    state = 4
                elif c and c.isdigit():
                    lexeme += c
                    self._advance()
                    state = 5
                else:
                    self._error(f"Sinal ou dígito esperado após 'e' no número '{lexeme}'")

            elif state == 4:  # Viu 'e[+-]', esperando dígito
                if c and c.isdigit():
                    lexeme += c
                    self._advance()
                    state = 5
                else:
                    self._error(f"Dígito esperado após sinal do expoente em '{lexeme}'")
            
            elif state == 5:  # Parte do expoente
                if c and c.isdigit():
                    lexeme += c
                    self._advance()
                else:
                    break  # Aceitação

        # Fim da máquina de estados, retorna o token NUM
        return Token(NUM, lexeme, start_line)

    def _string_literal(self):
        """
        Processa um literal string ou caractere.
        Strings em Pascal usam ' e escapam ' com ''.
        Ex: 'O''l''a' -> "O'l'a"
        """
        content = ""
        start_line = self.line
        
        self._advance()  # Consome o ' de abertura
        
        while True:
            if self.current_char is None:
                self._error("String literal não finalizada.")
            
            elif self.current_char == "'":
                # Encontramos uma aspa
                if self._peek() == "'":
                    # É um escape: ''
                    content += "'"
                    self._advance()  # Consome o primeiro '
                    self._advance()  # Consome o segundo '
                else:
                    # É o fim do literal
                    self._advance()  # Consome o ' de fechamento
                    break  # Sai do loop
            else:
                # Caractere normal
                content += self.current_char
                self._advance()
        
        # O C diferencia CAR de LITERAL pelo tamanho (ex: 'a' vs 'abc')
        # 'a' (tamanho 3 no C) -> len(content) == 1 aqui
        # '''' (tamanho 4 no C) -> len(content) == 1 aqui
        if len(content) == 1:
            return Token(CAR, content, start_line)
        else:
            return Token(LITERAL, content, start_line)

    def get_next_token(self):
        """
        Função principal que obtém o próximo token do código-fonte.
        Esta é a função que o "compilador" (Parser) chamaria.
        """
        
        # O loop principal é o coração do lexer, assim como no C
        while self.current_char is not None:
            
            # 1. Pular espaços em branco e novas linhas
            if self.current_char in ' \t\n':
                self._skip_whitespace()
                continue
                
            # 2. Pular comentários
            if self.current_char in '{(' and self._skip_comment():
                continue

            # --- Reconhecimento de Tokens ---

            # 3. Identificadores e Palavras-chave
            # (Regra: começa com letra)
            if self.current_char.isalpha():
                return self._id_or_keyword()
            
            # 4. Números
            # (Regra: começa com dígito)
            if self.current_char.isdigit():
                return self._number()
            
            # 5. Strings e Caracteres
            if self.current_char == "'":
                return self._string_literal()

            # 6. Operadores e Pontuação (um a um)
            
            # Operador de atribuição :=
            if self.current_char == ':' and self._peek() == '=':
                start_line = self.line
                self._advance()
                self._advance()
                return Token(OPASIGNA, ':=', start_line)

            # Operador relacional <> (diferente)
            if self.current_char == '<' and self._peek() == '>':
                start_line = self.line
                self._advance()
                self._advance()
                return Token(OPREL, '<>', start_line)

            # Operador relacional <=
            if self.current_char == '<' and self._peek() == '=':
                start_line = self.line
                self._advance()
                self._advance()
                return Token(OPREL, '<=', start_line)

            # Operador relacional >=
            if self.current_char == '>' and self._peek() == '=':
                start_line = self.line
                self._advance()
                self._advance()
                return Token(OPREL, '>=', start_line)

            # Operadores de caractere único
            # (Um dicionário para mapear caracteres a tipos de token)
            single_char_tokens = {
                '<': OPREL,
                '>': OPREL,
                '=': OPREL,
                '+': OPSUMA,
                '-': OPSUMA,
                '*': OPMULT,
                '/': OPMULT,
                ';': PONTO_VIRG,
                ',': VIRGULA,
                '.': PONTO,
                ':': DOIS_PONTOS,
                '(': ABRE_PAR,
                ')': FECHA_PAR,
                '[': ABRE_COL,
                ']': FECHA_COL,
            }
            
            token_type = single_char_tokens.get(self.current_char)
            if token_type:
                lexeme = self.current_char
                start_line = self.line
                self._advance()
                return Token(token_type, lexeme, start_line)

            # 7. Caractere não reconhecido
            self._error(f"Caractere inesperado: '{self.current_char}'")
        
        # Se o loop terminar (self.current_char é None), retornamos EOF
        return Token(EOF, 'EOF', self.line)