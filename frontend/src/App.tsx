import { ChakraProvider, Container, VStack, Heading, Text, useColorModeValue } from '@chakra-ui/react';
import DrugInteractionForm from './components/DrugInteractionForm';

function App() {
  const bgColor = useColorModeValue('gray.50', 'gray.900');

  return (
    <ChakraProvider>
      <Container maxW="container.xl" py={8} minH="100vh" bg={bgColor}>
        <VStack spacing={8} align="stretch">
          <Heading as="h1" size="xl" textAlign="center" color="blue.600">
            Drug Interaction Assistant
          </Heading>
          <Text textAlign="center" color="gray.600">
            Ask me about drug interactions or side effects
          </Text>

          <DrugInteractionForm />
        </VStack>
      </Container>
    </ChakraProvider>
  );
}

export default App;
