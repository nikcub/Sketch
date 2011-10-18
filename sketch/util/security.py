
import hashlib

def bcrypt(password, salt = "abcdefghijklmnopqrstuvwxyz", iterations=5000):
  h = hashlib.sha1()
  h.update(password)
  h.update(salt)
  for x in range(iterations):
    h.update(h.digest())
  return h.hexdigest()

def file_hash(filedata):
  return hashlib.sha1(filedata).hexdigest()

def generate_password(length = 10, num_punc = 1, sequence = None):
  """
  Generate a random password, where:

  :var    length      length of password, default 10
  :var    num_punc    minimum number of punctuation characters in pass
  :var    sequence    the sequence to generate from. vary to increase or decrease frequency of each
  """
  numbers = [chr(i) for i in range(48, 58)]
  uppercase = [chr(i) for i in range(65, 91)]
  lowercase = [chr(i) for i in range(97, 123)]
  punc = [chr(i) for i in [33, 35, 36, 42, 43, 46, 47, 64, 95]]
  vowels = ['a','e','i','o','u']
  sequence = ['lowercase', 'lowercase', 'lowercase', 'lowercase', 'vowels', 'numbers', 'uppercase', 'lowercase', 'punc', 'vowels']
  seq = [sequence[random.randint(0, len(sequence) - 1)] for i in range(0, 1000)]
  return "".join([locals()[i][random.randint(0, len(locals()[i]) - 1)] for i in seq])[0:length]
