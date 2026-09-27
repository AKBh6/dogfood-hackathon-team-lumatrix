generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "sqlite"
  url      = env("DATABASE_URL")
}

model User {
  id       String  @id @default(uuid())
  email    String  @unique
  password String  // Hashed
  role     String  // "PARTICIPANT", "JUDGE", "ORGANIZER", "ADMIN"
  teamId   String?
  team     Team?   @relation(fields: [teamId], references: [id])
  ballots  Ballot[]
}

model Team {
  id         String   @id @default(uuid())
  name       String
  inviteCode String   @unique
  members    User[]
  project    Project?
}

model Project {
  id          String   @id @default(uuid())
  title       String
  description String
  repoUrl     String
  isDraft     Boolean  @default(true)
  teamId      String   @unique
  team        Team     @relation(fields: [teamId], references: [id])
  ballots     Ballot[]
}

model Ballot {
  id          String  @id @default(uuid())
  judgeId     String
  judge       User    @relation(fields: [judgeId], references: [id])
  projectId   String
  project     Project @relation(fields: [projectId], references: [id])
  scoreTech   Int     // 1-5 scale
  scoreDesign Int
  scoreIdea   Int
  rawTotal    Int
  zScore      Float?  // Populated during normalization
  
  @@unique([judgeId, projectId])
}
