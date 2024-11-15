import hashlib

from functools import lru_cache

from utils.tokenizer import tokenize
from utils.constants import CONFIG

class SimHash:
    def __init__(self, b=128):
        self.b = b  # Number of bits in the fingerprint

    @lru_cache(maxsize=CONFIG['simhash_cache_size'])
    def _hash_word(self, word):
        encoded_word = word.encode('utf-8') # Encode the word into bytes using UTF-8 encoding
        md5_hash = hashlib.md5()            # Create an MD5 hash object
        md5_hash.update(encoded_word)       # Update the hash object with the encoded word
        hex_digest = md5_hash.hexdigest()   # Get the hexadecimal digest of the hash
        hash_value = int(hex_digest, 16)    # Convert the hexadecimal digest to an integer with base 16
        return bin(hash_value)[2:].zfill(self.b)[-self.b:]  # Convert hash value to binary and ensure it is b bits long

    def _calculate_frequencies(self, tokens):
        # Calculate word frequencies
        freq = {}
        for token in tokens:
            if token in freq:
                freq[token] += 1
            else:
                freq[token] = 1
        return freq


    def compute_simhash(self, text):
        tokens = tokenize(text)
        frequencies = self._calculate_frequencies(tokens)
        
        V = [0] * self.b
        
        for word, weight in frequencies.items():
            hash_value = self._hash_word(word)
            for i in range(self.b):
                if hash_value[i] == '1':
                    V[i] += weight
                else:
                    V[i] -= weight
        
        fingerprint = ''.join(['1' if v > 0 else '0' for v in V])
        return fingerprint

    def hamming_distance(self, hash1, hash2):
        # Calculate the Hamming distance between two hashes
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))

    def similarity(self, text1, text2):
        hash1 = self.compute_simhash(text1)
        hash2 = self.compute_simhash(text2)
        distance = self.hamming_distance(hash1, hash2)
        return 1 - distance / self.b

    def are_near_duplicates(self, text1, text2, threshold=0.8):
        return self.similarity(text1, text2) >= threshold


# Test the SimHash class
# simhasher = SimHash()

# text1 = """
# Informatics Professors Sam Malek and Joshua Garcia recently started working on a three year 1 66 million grant from the National Science Foundation The grant Constructing a Community Wide Software Architecture Infrastructure is a collaborative project involving faculty from UCI the University of Southern California and the Rochester Institute of Technology Malek and Garcia will lead the UCI team comprised of graduate student researchers working out of the Institute for Software Research ISR The goal is to develop the Software Architecture INstrument SAIN a first of its kind integration framework for assembling architecture related tools and techniques enabling empirical research in the context of software maintenance As outlined in the grant proposal SAIN has the potential to transform software architecture research and practice by 1 facilitating the discovery and adoption of cutting edge techniques and tools that are best suited to modern problems and 2 ensuring architecture s central role in a broad range of software engineering activities According to Malek the UCI team will be responsible for developing several architectural recovery techniques and making them available for use as part of an integrated tool suite We will also empirically study architectural change decay and maintenance issues in a variety of open source and commercial software projects He goes on to note that the final part of UCI s effort will be to construct and curate the largest repository of architectural artifacts to facilitate research and enable reproducibility of results Shani Murray
# """
# text2 = """
# February 15 2019 The Herman P Sophia Taubman Foundation has provided a generous gift of 1 4 million to UCI s Cybersecurity Policy Research Institute CPRI led by Executive Director Bryan Cunningham Founded in the 1960s by the six children of Herman and Sophia Taubman the foundation aims to promote the advancement of scientific research higher education and community philanthropy Six Taubman cousins manage the foundation including attorney Perry Taubman currentlya visiting scholar at UC San Diego researching autonomous agents for medical diagnosis and insurance coding Taubman and his cousins understand the crucial need for research focused on cybersecurity and the emerging Internet of Everything IoE that is the interaction between the traditional internet and the hundreds of millions of connected Internet of Things IoT devices The board members of the foundation have professional careers in law technology medicine and infrastructure finance says Taubman We have all been concerned for a long time about cybersecurity in terms of our professional fields and as citizens on the level of national security Consequently the foundation was seeking ways to advance practical solutions in this area I personally looked at the cybersecurity research programs at a number of universities and felt that CPRI under Bryan Cunningham s leadership had a uniquely suited focus around all of these areas Cunningham is excited about this partnership to secure the seams of the IoE As he notes we could not be more thrilled with the Taubman family s support and with Perry s participation in our efforts Drawing on UCI s multidisciplinary expertise these new IoE efforts aim to fill a void in current cybersecurity related research and policy and technical solutions development Our very strong team will address important and pressing issues affecting not only the privacy and security of individuals but also our country s economic and national security he explains This mission is squarely in CPRI s wheelhouse The foundation s gift will provide resources to support three new CPRI projects focused on the IoT and IoE Computer Science Professor Ian Harris is leading efforts to perform IoT IoE technical testing and develop an IoE Cyber Test Range on the UCI campus and Computer Science Professor Scott Jordan is heading up research into regulation and standards setting UCI Law Professor Shauhin Talesh is exploring the emerging role of insurance companies as de facto cyber regulators Cunningham will act as the overall lead for the interrelated projects All of these areas are critical for advancing cybersecurity says Taubman Furthermore the projects address his two main concerns surrounding IoE the lack of standards and the difficulty in securing embedded systems This requires expertise in engineering that is very different from traditional security he explains We found a unique team on the technical side with Ian and Scott who were able to approach the problem from both an engineering and policy perspective The gift will provide funding for Ph D candidate researchers facilities and equipment for IoE testing data analysis support and standards and policy development It will also support undergraduate research and education enable CPRI and its team to hold multiple conferences and support UCI students in cybersecurity Capture the Flag competitions All of this fits well with the Taubman Foundation s goal of supporting scientific research and higher education in an effort to build a more security minded engineering culture Our vision is that security will become a fundamental concern of engineers and companies for every relevant device as opposed to an afterthought says Taubman There is a critical shortage of security engineers right now that needs to be addressed by higher education but even more important is developing a culture of security engineering in all who graduate from our schools of engineering Shani Murray
# """

# hash1 = simhasher.compute_simhash(text1)
# hash2 = simhasher.compute_simhash(text2)

# distance = simhasher.hamming_distance(hash1, hash2)

# similarity = simhasher.similarity(text1, text2)
# near_duplicates = simhasher.are_near_duplicates(text1, text2)

# print(f"Hash 1: {hash1}")
# print(f"Hash 2: {hash2}")

# print(f"Hamming Distance: {distance}")
# print(f"Similarity: {similarity}")
# print(f"Near Duplicates: {near_duplicates}")


# def same_tokens_in_boths(text1, text2):
#     tokens1 = tokenize(text1)
#     tokens2 = tokenize(text2)
    
#     s1 = set(tokens1)
#     s2 = set(tokens2)

#     return s1.intersection(s2)

# print(same_tokens_in_boths(text1, text2))