# create a class for a personne that needs to do squats 
class Personne:
    def __init__(self, name, objectif,done):
        self.name = name
        self.objectif = objectif
        self.done = done
    
    def squats(self):
        print(f"{self.name} is doing squats")