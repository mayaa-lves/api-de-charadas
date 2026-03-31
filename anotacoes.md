# endpoints url

## Endpoints públicos (open)
- GET -  /charadas - (todas as charadas)
- GET - /charadas/aleatoria - (1 charada sorteada)
- GET - /charadas/id - (1 charada pelo id)

## Endpoints Privados (Autentificação Bearer)
POST - /charadas - (Criar uma nova charada)
PATCH - /charadas/<int:id> - (Alterar parcialmente pelo id)
PUT - /charadas/<int:id> - (Alterar inteiramente pelo id)
DELETE - /charadas/<int:id> - (Apagar 1 charada pelo id)


#### Database: Firebase Firestoreda Google (NO-SQL - Nã relacional)
#### HOST: Vercel
