# 🖼️ Conversor e Compactador de Imagens

Uma ferramenta desenvolvida em **Python** para converter e/ou compactar imagens em lote de forma simples e rápida.

O script suporta os formatos **JPG**, **JPEG**, **PNG**, **HEIC**, **HEIF** e **WEBP**, permitindo converter imagens para WebP, compactá-las mantendo o formato original ou realizar ambas as operações simultaneamente.

## ✨ Funcionalidades

* Conversão de imagens para **WebP**.
* Compactação de imagens mantendo o formato original.
* Conversão e compactação em uma única execução.
* Processamento em lote de múltiplas imagens.
* Suporte aos formatos:

  * JPG
  * JPEG
  * PNG
  * HEIC
  * HEIF
  * WEBP
* Qualidade da compactação configurável.
* Criação automática da pasta de saída.
* Validação do arquivo gerado antes da exclusão do original.
* Opção para manter os arquivos originais.

---

## 🛠️ Tecnologias utilizadas

* Python 3
* Pillow
* pillow-heif
* argparse
* pathlib

---

## 📦 Instalação

Clone este repositório:

```bash
git clone https://github.com/SEU-USUARIO/SEU-REPOSITORIO.git
```

Acesse a pasta do projeto:

```bash
cd SEU-REPOSITORIO
```

Instale as dependências:

```bash
pip install Pillow pillow-heif
```

---

## 🚀 Como utilizar

O script utiliza três parâmetros obrigatórios:

* `--entrada` → Pasta contendo as imagens.
* `--saida` → Pasta onde serão salvos os arquivos processados.
* `--modo` → Define a operação desejada.

### Converter apenas para WebP

Mantém alta qualidade, alterando apenas o formato da imagem.

```bash
python converter_imagens.py --entrada ./entrada --saida ./saida --modo converter
```

---

### Compactar mantendo o formato original

Reduz a qualidade da imagem (70 por padrão).

```bash
python converter_imagens.py --entrada ./entrada --saida ./saida --modo compactar
```

---

### Converter para WebP e compactar

Converte para WebP e aplica a qualidade definida.

```bash
python converter_imagens.py --entrada ./entrada --saida ./saida --modo ambos
```

---

## 🎚️ Ajustando a qualidade

É possível definir a qualidade da imagem utilizando o parâmetro `--qualidade`.

Exemplo:

```bash
python converter_imagens.py --entrada ./entrada --saida ./saida --modo ambos --qualidade 80
```

Valor padrão:

```text
70
```

Intervalo permitido:

```text
0 até 100
```

Quanto maior o valor, maior a qualidade e o tamanho final do arquivo.

---

## 📂 Manter os arquivos originais

Por padrão, o programa remove os arquivos da pasta de entrada **somente após validar que o arquivo processado foi criado com sucesso**.

Caso deseje manter os arquivos originais, utilize:

```bash
python converter_imagens.py --entrada ./entrada --saida ./saida --modo ambos --manter-original
```

---

## 📁 Estrutura sugerida

```
projeto/
│
├── entrada/
│   ├── imagem1.jpg
│   ├── imagem2.png
│   └── imagem3.heic
│
├── saida/
│
├── converter_imagens.py
└── README.md
```

---

## ✅ Exemplo de execução

```text
Pasta de entrada: C:\Imagens\Entrada
Pasta de saída:   C:\Imagens\Saida

Encontradas 12 imagem(ns).

Modo: ambos

Qualidade: 70

OK: foto01.jpg -> foto01.webp
OK: foto02.png -> foto02.webp
OK: foto03.heic -> foto03.webp

Processo concluído!
```

---

## 📄 Licença

Este projeto está disponível sob a licença MIT.
